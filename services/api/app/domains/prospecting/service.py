import logging
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis
from sqlalchemy import and_, func, select

from app.config.settings import settings
from app.domains.auth.models import User
from app.domains.businesses.models import Business
from app.domains.prospecting.models import DiscoveryJob, DiscoveryTask, JobStatus, TaskStatus
from app.domains.prospecting.schemas import (
    JobCreateResponse,
    JobStatusResponse,
    ProspectingQuery,
)
from app.shared.exceptions import ConflictError, EntityNotFoundError

logger = logging.getLogger("fastui.prospecting")

# Stream key — must match the worker's STREAM_DISCOVERY_TASKS constant.
_STREAM_DISCOVERY_TASKS = "fastui:discover:tasks"

# Shared Redis client for the API Control Plane
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def build_location_string(location_data: Any) -> str:
    """Builds a canonical location string from a structured location dict, string, or list."""
    if isinstance(location_data, str):
        return location_data.strip()
    if isinstance(location_data, list):
        return ", ".join([str(x).strip() for x in location_data if str(x).strip()])
    if isinstance(location_data, dict):
        parts = []
        for key in ["locality", "city", "state", "country"]:
            val = location_data.get(key)
            if val and str(val).strip():
                parts.append(str(val).strip())
        return ", ".join(parts) if parts else ""
    return ""


async def count_existing_prospects_for_scope(session: Any, category: str, city: str | None) -> int:
    """Counts unique existing businesses matching category and location scope."""
    conditions = []
    if category and category.lower() not in ("businesses", "business"):
        conditions.append(func.lower(Business.category) == category.lower())
    if city:
        conditions.append(func.lower(Business.city) == city.lower())

    query = select(func.count(Business.id))
    if conditions:
        query = query.where(and_(*conditions))

    result = await session.execute(query)
    return result.scalar() or 0


class ProspectingService:
    """Control Plane Service managing discovery jobs and tasks."""

    @staticmethod
    async def create_job(
        session: Any,
        query: ProspectingQuery,
        user: User,
    ) -> JobCreateResponse:
        """Creates a job, initial task, and enqueues it to Redis."""
        query_dict = query.model_dump()
        loc_raw = query_dict.get("location") or query_dict.get("locations")
        location_str = build_location_string(loc_raw) or "Global"
        target_audience = (
            query_dict.get("target_audience")
            or query_dict.get("business_type")
            or "Businesses"
        )

        # Optionally pre-count existing, though it's not strictly required
        # for distributed mode. We do it for immediate progress feedback.
        loc_city = None
        if isinstance(loc_raw, dict):
            loc_city = loc_raw.get("city")
        elif isinstance(loc_raw, str):
            parts = [p.strip() for p in loc_raw.split(",") if p.strip()]
            if len(parts) >= 1:
                loc_city = parts[0]

        existing_unique = await count_existing_prospects_for_scope(session, target_audience, loc_city)

        job = DiscoveryJob(
            user_id=user.id,
            query=query_dict,
            status=JobStatus.QUEUED,
            existing_businesses=existing_unique,
            started_at=datetime.now(UTC),
        )
        session.add(job)
        await session.flush()

        task_params = {
            "target_audience": target_audience,
            "location": location_str,
            "limit": query_dict.get("target_count") or query_dict.get("limit") or 1000,
            "batch_size": 50,
            "cursor": None,
        }

        task = DiscoveryTask(
            job_id=job.id,
            status=TaskStatus.PENDING,
            params=task_params,
        )
        session.add(task)
        await session.commit()
        await session.refresh(job)
        await session.refresh(task)

        try:
            await redis_client.xadd(
                _STREAM_DISCOVERY_TASKS,
                {"task_id": str(task.id), "job_id": str(job.id)}
            )
            job.status = JobStatus.RUNNING
            await session.commit()
            logger.info(f"Enqueued initial DiscoveryTask {task.id} for Job {job.id}")
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.id} to Redis: {e}. Reconciliation will retry.")

        return JobCreateResponse(job_id=str(job.id), status=job.status.value)

    @staticmethod
    async def get_job_status(session: Any, job_id: int) -> JobStatusResponse:
        """Polls current status and progress metrics derived from DB."""
        job = await session.get(DiscoveryJob, job_id)
        if not job:
            raise EntityNotFoundError("DiscoveryJob", job_id)

        target_count = int((job.query or {}).get("target_count") or (job.query or {}).get("limit") or 1000)
        total_scope_leads = (job.existing_businesses or 0) + (job.new_leads or 0)
        remaining_count = max(0, target_count - total_scope_leads)

        # Determine completion based on task state if job isn't already terminal
        if job.status not in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            stmt = select(DiscoveryTask.status).where(DiscoveryTask.job_id == job.id)
            result = await session.execute(stmt)
            task_statuses = result.scalars().all()

            active_tasks = [s for s in task_statuses if s in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING)]
            failed_tasks = [s for s in task_statuses if s in (TaskStatus.FAILED, TaskStatus.DEAD_LETTER)]

            # Only fail the job if all tasks failed and no tasks remain active
            if failed_tasks and len(failed_tasks) == len(task_statuses) and not active_tasks:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(UTC)
                await session.commit()
            # If all tasks succeeded and results have been committed (total_processed > 0),
            # reconcile completion if not already marked completed by the result processor.
            elif not active_tasks and not failed_tasks and task_statuses and job.total_processed > 0:
                job.progress_percent = 100
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                await session.commit()

        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status.value,
            progress_percent=job.progress_percent,
            total_discovered=job.total_discovered,
            total_processed=job.total_processed,
            new_leads=job.new_leads,
            existing_businesses=job.existing_businesses,
            duplicates=job.duplicates,
            skipped=job.skipped,
            errors=job.errors,
            target_count=target_count,
            remaining_count=remaining_count,
            error_message=job.error_message,
        )

    @staticmethod
    async def cancel_job(session: Any, job_id: int) -> DiscoveryJob:
        """Cancels a job and marks pending/running tasks as failed/cancelled."""
        job = await session.get(DiscoveryJob, job_id)
        if not job:
            raise EntityNotFoundError("DiscoveryJob", job_id)

        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            raise ConflictError(f"Job {job_id} cannot be cancelled — already {job.status.value}")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)

        # Cancel active tasks
        stmt = select(DiscoveryTask).where(
            DiscoveryTask.job_id == job.id,
            DiscoveryTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING])
        )
        result = await session.execute(stmt)
        for task in result.scalars():
            task.status = TaskStatus.FAILED
            task.error_message = "Cancelled by user"

        await session.commit()
        await session.refresh(job)
        logger.info(f"Discovery job {job_id} marked as CANCELLED.")
        return job
