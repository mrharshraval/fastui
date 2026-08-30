"""
FastUI Standalone Background Worker Subsystem (FAANG Standard)
=============================================================
Autonomous, horizontally scalable worker daemon designed to run as an
independent service on cloud providers (Render, AWS ECS, Fly.io, Kubernetes).

Responsibilities:
-----------------
1. Consumes queued discovery jobs from the shared database.
2. Manages headless Chromium instances via Playwright for resilient web extraction.
3. Performs name normalization and entity deduplication.
4. Persists extracted business records and logs lifecycle activities.
5. Implements graceful shutdown (SIGINT/SIGTERM), concurrency control, and telemetry.
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Ensure project modules are importable
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
SERVICES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
API_DIR = os.path.abspath(os.path.join(SERVICES_DIR, "api"))

for path in [CURRENT_DIR, SERVICES_DIR, API_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from worker.core.config import worker_settings
    from worker.contracts import DiscoverySearchParams
    from worker.deduplication import LeadDeduplicator
    from worker.normalizers import BusinessNameNormalizer
    from worker.sources.aggregator import MultiSourceDiscoveryAggregator
except ImportError:
    from core.config import worker_settings
    from contracts import DiscoverySearchParams
    from deduplication import LeadDeduplicator
    from normalizers import BusinessNameNormalizer
    from sources.aggregator import MultiSourceDiscoveryAggregator

try:
    from models.schema import (
        Activity,
        ActivityType,
        Business,
        DiscoveryJob,
        JobStatus,
        WebsiteStatus,
    )
except ImportError:
    # Direct model import fallback
    from api.models.schema import (
        Activity,
        ActivityType,
        Business,
        DiscoveryJob,
        JobStatus,
        WebsiteStatus,
    )

logging.basicConfig(
    level=getattr(logging, worker_settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [worker] %(name)s: %(message)s",
)
logger = logging.getLogger("fastui.worker")


def build_location_string(location_data: Any) -> str:
    """Builds a canonical location string from structured location dictionary, string, or list."""
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


class StandaloneDiscoveryWorker:
    """
    Autonomous discovery worker processing asynchronous scraping tasks from the database queue.
    """

    def __init__(self):
        self.settings = worker_settings
        self.semaphore = asyncio.Semaphore(self.settings.MAX_CONCURRENT_SCRAPERS)
        self.running = False
        self._active_tasks: set[asyncio.Task] = set()

        connect_args = {}
        if "sqlite" in self.settings.DATABASE_URL:
            connect_args["check_same_thread"] = False

        self.engine = create_async_engine(
            self.settings.DATABASE_URL,
            echo=self.settings.DEBUG,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def process_job(self, job_id: int) -> None:
        """
        Executes an isolated scraping and ingestion job.
        """
        async with self.semaphore:
            async with self.SessionLocal() as session:
                job = await session.get(DiscoveryJob, job_id)
                if not job or job.status != JobStatus.QUEUED:
                    return

                try:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now(timezone.utc)
                    await session.commit()
                    logger.info(f"[Job {job_id}] Started discovery execution.")

                    query_dict = job.query if isinstance(job.query, dict) else {}
                    loc_raw = query_dict.get("location") or query_dict.get("locations")
                    location_str = build_location_string(loc_raw) or "Global"
                    target_audience = (
                        query_dict.get("target_audience")
                        or query_dict.get("business_type")
                        or "Businesses"
                    )
                    limit_count = query_dict.get("limit") or 20

                    search_params = DiscoverySearchParams(
                        target_audience=target_audience,
                        location=location_str,
                        limit=limit_count,
                    )

                    aggregator = MultiSourceDiscoveryAggregator(headless=self.settings.HEADLESS_BROWSER)
                    raw_leads = await aggregator.discover(search_params)

                    # Check for mid-scrape cancellation
                    await session.refresh(job)
                    if job.status == JobStatus.CANCELLED:
                        logger.info(f"[Job {job_id}] Job cancelled during extraction. Discarding results.")
                        return

                    job.total_discovered = len(raw_leads)

                    # Resolve location components
                    loc_city, loc_state, loc_country = None, None, None
                    if isinstance(loc_raw, dict):
                        loc_city = loc_raw.get("city")
                        loc_state = loc_raw.get("state") or loc_raw.get("region")
                        loc_country = loc_raw.get("country")
                    elif isinstance(loc_raw, str):
                        parts = [p.strip() for p in loc_raw.split(",") if p.strip()]
                        if len(parts) == 1:
                            loc_city = parts[0]
                        elif len(parts) == 2:
                            loc_city, loc_country = parts
                        elif len(parts) >= 3:
                            loc_city, loc_state, loc_country = parts[0], parts[1], parts[2]

                    for lead in raw_leads:
                        name_norm = BusinessNameNormalizer.normalize(lead.name)
                        norm_phone = LeadDeduplicator.normalize_phone(lead.phone)
                        norm_web = LeadDeduplicator.normalize_website(lead.website)

                        duplicate = await LeadDeduplicator.is_duplicate(
                            session,
                            norm_phone,
                            norm_web,
                            name_norm.display_name,
                            loc_city or lead.city,
                        )

                        if duplicate:
                            job.duplicates += 1
                        else:
                            web_status = WebsiteStatus.WEBSITE_FOUND if lead.website else WebsiteStatus.NO_WEBSITE
                            new_business = Business(
                                business_name=name_norm.display_name,
                                raw_business_name=name_norm.raw_name,
                                normalized_business_name=name_norm.normalized_name,
                                category=lead.category or target_audience,
                                address=lead.address,
                                city=loc_city or lead.city,
                                state=loc_state or lead.state,
                                country=loc_country or lead.country,
                                phone=norm_phone or lead.phone,
                                website=lead.website,
                                website_status=web_status,
                                rating=lead.rating,
                                reviews_count=lead.reviews_count,
                                is_lead=False,
                                qualification_status="unqualified",
                                source_platform="google_maps",
                            )
                            session.add(new_business)
                            await session.flush()

                            # Initial discovery activity log
                            init_act = Activity(
                                business_id=new_business.id,
                                type=ActivityType.NOTE_ADDED,
                                channel="system",
                                outcome="Prospect Discovered",
                                notes=f"Discovered via search for '{target_audience}' in '{location_str}'",
                            )
                            session.add(init_act)
                            job.new_leads += 1

                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    logger.info(f"[Job {job_id}] Successfully completed: {job.new_leads} new prospects saved, {job.duplicates} duplicates skipped.")

                except Exception as exc:
                    logger.exception(f"[Job {job_id}] Failed with error: {exc}")
                    await session.rollback()
                    try:
                        job = await session.get(DiscoveryJob, job_id)
                        if job:
                            job.status = JobStatus.FAILED
                            job.completed_at = datetime.now(timezone.utc)
                            job.error_message = str(exc)
                            await session.commit()
                    except Exception as commit_err:
                        logger.error(f"[Job {job_id}] Failed to record error state: {commit_err}")

    async def fetch_next_queued_job_id(self) -> Optional[int]:
        """
        Pulls the next QUEUED job ID safely from the database.
        """
        async with self.SessionLocal() as session:
            stmt = (
                select(DiscoveryJob.id)
                .where(DiscoveryJob.status == JobStatus.QUEUED)
                .order_by(DiscoveryJob.created_at.asc())
                .limit(1)
            )
            # Use FOR UPDATE SKIP LOCKED on PostgreSQL for multi-worker concurrency
            if "postgresql" in self.settings.DATABASE_URL or "postgres" in self.settings.DATABASE_URL:
                stmt = stmt.with_for_update(skip_locked=True)

            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def start(self) -> None:
        """
        Main worker polling loop.
        """
        self.running = True
        logger.info(f"FastUI Standalone Discovery Worker started (Concurrency limit: {self.settings.MAX_CONCURRENT_SCRAPERS}).")

        while self.running:
            try:
                job_id = await self.fetch_next_queued_job_id()
                if job_id:
                    task = asyncio.create_task(self.process_job(job_id))
                    self._active_tasks.add(task)
                    task.add_done_callback(self._active_tasks.discard)
                else:
                    await asyncio.sleep(self.settings.JOB_POLL_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker polling loop: {e}", exc_info=True)
                await asyncio.sleep(self.settings.JOB_POLL_INTERVAL_SECONDS)

        logger.info("Worker polling loop stopped.")

    async def stop(self) -> None:
        """
        Gracefully drains active scraping jobs and closes database connections.
        """
        logger.info("Initiating graceful worker shutdown...")
        self.running = False

        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} ongoing scraping tasks to finish...")
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        await self.engine.dispose()
        logger.info("FastUI Discovery Worker stopped successfully.")


async def main():
    worker = StandaloneDiscoveryWorker()

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler(sig):
        logger.info(f"Received signal {signal.Signals(sig).name}. Triggering shutdown...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: _signal_handler(s))
        except NotImplementedError:
            # Signal handling on Windows
            pass

    worker_task = asyncio.create_task(worker.start())

    await stop_event.wait()
    await worker.stop()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker process exited.")
