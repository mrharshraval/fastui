"""FastUI Prospecting Domain Service.

Orchestrates discovery jobs, worker scraping batch dispatch, and incremental persistence.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select

from app.domains.auth.models import User
from app.domains.businesses.deduplication import LeadDeduplicator
from app.domains.businesses.models import Business, BusinessSource, WebsiteStatus
from app.domains.businesses.normalizer import BusinessNameNormalizer
from app.domains.engagement.models import Activity, ActivityType
from app.domains.prospecting.models import DiscoveryJob, JobStatus
from app.domains.prospecting.schemas import (
    JobCreateResponse,
    JobStatusResponse,
    ProspectingQuery,
)
from app.infrastructure.database.session import get_db_session
from app.infrastructure.external.worker_client import (
    WorkerClient,
    WorkerDiscoveryParams,
)
from app.shared.exceptions import ConflictError, EntityNotFoundError
from app.shared.phone import is_mobile_phone

logger = logging.getLogger("fastui.prospecting")

DEFAULT_BATCH_SIZE = 50


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
    """Service managing discovery jobs, scraper orchestration, and lead ingestion."""

    @staticmethod
    async def create_job(
        session: Any,
        query: ProspectingQuery,
        user: User,
    ) -> JobCreateResponse:
        """Enqueues a new lead discovery job."""
        job = DiscoveryJob(
            user_id=user.id,
            query=query.model_dump(),
            status=JobStatus.QUEUED,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return JobCreateResponse(job_id=str(job.id), status=job.status.value)

    @staticmethod
    async def get_job_status(session: Any, job_id: int) -> JobStatusResponse:
        """Polls current status and progress metrics of a discovery job."""
        job = await session.get(DiscoveryJob, job_id)
        if not job:
            raise EntityNotFoundError("DiscoveryJob", job_id)

        target_count = int(
            (job.query or {}).get("target_count") or (job.query or {}).get("limit") or 1000
        )
        total_scope_leads = (job.existing_businesses or 0) + (job.new_leads or 0)
        remaining_count = max(0, target_count - total_scope_leads)

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
        """Cancels a queued or currently running discovery job."""
        job = await session.get(DiscoveryJob, job_id)
        if not job:
            raise EntityNotFoundError("DiscoveryJob", job_id)

        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            raise ConflictError(f"Job {job_id} cannot be cancelled — already {job.status.value}")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(job)
        logger.info(f"Discovery job {job_id} marked as CANCELLED.")
        return job

    @staticmethod
    async def process_job(job_id: int) -> None:
        """Background task: dispatches batches to worker, deduplicates, and persists."""
        async with get_db_session() as session:
            job = await session.get(DiscoveryJob, job_id)
            if not job or job.status != JobStatus.QUEUED:
                return

            try:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(UTC)
                await session.commit()

                query_dict = job.query if isinstance(job.query, dict) else {}
                loc_raw = query_dict.get("location") or query_dict.get("locations")
                location_str = build_location_string(loc_raw) or "Global"
                target_audience = (
                    query_dict.get("target_audience")
                    or query_dict.get("business_type")
                    or "Businesses"
                )
                target_count = int(
                    query_dict.get("target_count") or query_dict.get("limit") or 1000
                )

                loc_city: str | None = None
                loc_state: str | None = None
                loc_country: str | None = None
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
                        loc_city = parts[0]
                        loc_state = parts[1]
                        loc_country = parts[2]

                existing_unique = await count_existing_prospects_for_scope(
                    session, target_audience, loc_city
                )
                job.existing_businesses = existing_unique
                await session.commit()

                remaining_count = max(0, target_count - existing_unique)
                if remaining_count <= 0:
                    job.progress_percent = 100
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(UTC)
                    await session.commit()
                    return

                current_cursor: str | None = None

                while remaining_count > 0 or current_cursor is not None:
                    await session.refresh(job)
                    if job.status == JobStatus.CANCELLED:
                        logger.info(f"Job {job_id} was cancelled. Stopping discovery loop.")
                        return

                    batch_limit = (
                        min(DEFAULT_BATCH_SIZE, remaining_count)
                        if remaining_count > 0
                        else DEFAULT_BATCH_SIZE
                    )
                    search_params = WorkerDiscoveryParams(
                        target_audience=target_audience,
                        location=location_str,
                        limit=batch_limit,
                        batch_size=batch_limit,
                        cursor=current_cursor,
                    )

                    worker_response = await WorkerClient.discover_batch(search_params)
                    batch_leads = worker_response.leads
                    current_cursor = worker_response.next_cursor

                    if not batch_leads and not current_cursor:
                        break

                    new_in_batch = 0
                    dups_in_batch = 0

                    for lead in batch_leads:
                        name_norm = BusinessNameNormalizer.normalize(lead.name)
                        norm_phone = LeadDeduplicator.normalize_phone(
                            lead.phone, location=location_str
                        )
                        norm_web = LeadDeduplicator.normalize_website(lead.website)

                        existing_biz = await LeadDeduplicator.find_duplicate(
                            session,
                            normalized_phone=norm_phone,
                            normalized_website=norm_web,
                            business_name=name_norm.display_name,
                            city=loc_city or lead.city,
                            source_platform=lead.source_platform,
                            source_place_id=lead.source_place_id,
                            address=lead.address,
                            postal_code=lead.postal_code,
                            latitude=lead.latitude,
                            longitude=lead.longitude,
                        )

                        display_phone = LeadDeduplicator.format_display_phone(
                            lead.phone, location=location_str
                        )
                        ext_place_id = (
                            getattr(lead, "google_place_id", None) or lead.source_place_id
                        )
                        ext_source_url = getattr(lead, "google_maps_url", None) or lead.source_url
                        raw_meta = {
                            "rating": lead.rating,
                            "reviews_count": lead.reviews_count,
                            "latitude": lead.latitude,
                            "longitude": lead.longitude,
                            "place_id": ext_place_id,
                            "google_maps_url": ext_source_url,
                            "opening_hours": lead.opening_hours,
                            "business_status": getattr(lead, "business_status", None),
                        }

                        if existing_biz:
                            job.duplicates += 1
                            dups_in_batch += 1

                            if not existing_biz.phone and display_phone:
                                existing_biz.phone = display_phone
                                existing_biz.normalized_phone = norm_phone
                            if not existing_biz.has_whatsapp:
                                if getattr(lead, "has_whatsapp", False) or is_mobile_phone(
                                    display_phone, location=location_str
                                ):
                                    existing_biz.has_whatsapp = True
                            if not existing_biz.website and lead.website:
                                existing_biz.website = lead.website
                                existing_biz.normalized_website = norm_web
                            if not existing_biz.email and lead.email:
                                existing_biz.email = lead.email
                            if not getattr(existing_biz, "postal_code", None) and lead.postal_code:
                                existing_biz.postal_code = lead.postal_code
                            if lead.category and (
                                not existing_biz.category
                                or existing_biz.category.lower() in ["businesses", "dentist"]
                            ):
                                existing_biz.category = lead.category

                            platform_name = lead.source_platform or "google_maps"
                            src_stmt = select(BusinessSource).where(
                                BusinessSource.business_id == existing_biz.id,
                                BusinessSource.platform == platform_name,
                            )
                            src_res = await session.execute(src_stmt)
                            existing_src = src_res.scalars().first()
                            if existing_src:
                                cur_payload = dict(existing_src.raw_payload or {})
                                for k, v in raw_meta.items():
                                    if v is not None and cur_payload.get(k) is None:
                                        cur_payload[k] = v
                                existing_src.raw_payload = cur_payload
                                if not existing_src.external_id and ext_place_id:
                                    existing_src.external_id = ext_place_id
                                if not existing_src.source_url and ext_source_url:
                                    existing_src.source_url = ext_source_url
                                existing_src.last_seen_at = datetime.now(UTC)
                            else:
                                new_src = BusinessSource(
                                    business_id=existing_biz.id,
                                    discovery_job_id=job.id,
                                    platform=platform_name,
                                    source_url=ext_source_url,
                                    external_id=ext_place_id,
                                    raw_payload=raw_meta,
                                )
                                session.add(new_src)
                        else:
                            web_status = (
                                WebsiteStatus.WEBSITE_FOUND
                                if lead.website
                                else WebsiteStatus.NO_WEBSITE
                            )
                            is_mobile = (
                                is_mobile_phone(display_phone, location=location_str)
                                if display_phone
                                else False
                            )
                            has_wa = bool(getattr(lead, "has_whatsapp", False) or is_mobile)

                            new_business = Business(
                                canonical_name=name_norm.display_name,
                                source_name=name_norm.raw_name,
                                business_name=name_norm.display_name,
                                raw_business_name=name_norm.raw_name,
                                normalized_business_name=name_norm.normalized_name,
                                category=lead.category or target_audience,
                                address=lead.address or location_str,
                                city=loc_city or lead.city or location_str,
                                state=loc_state or lead.state,
                                postal_code=lead.postal_code,
                                country=loc_country or lead.country,
                                phone=display_phone,
                                email=lead.email,
                                website=lead.website,
                                normalized_phone=norm_phone,
                                normalized_website=norm_web,
                                has_whatsapp=has_wa,
                                website_status=web_status,
                                qualification_status="unqualified",
                                source_platform=lead.source_platform or "google_maps",
                            )
                            session.add(new_business)
                            await session.flush()

                            business_source = BusinessSource(
                                business_id=new_business.id,
                                discovery_job_id=job.id,
                                platform=lead.source_platform or "google_maps",
                                source_url=ext_source_url,
                                external_id=ext_place_id,
                                raw_payload=raw_meta,
                            )
                            session.add(business_source)

                            discovery_activity = Activity(
                                business_id=new_business.id,
                                user_id=job.user_id,
                                type=ActivityType.BUSINESS_DISCOVERED,
                                channel=lead.source_platform or "google_maps",
                                outcome="Discovered via prospecting scraper",
                                notes=f"Discovered during job {job.id} for '{target_audience}' in '{location_str}'",
                                entity_type="discovery_job",
                                entity_id=job.id,
                                created_at=datetime.now(UTC),
                            )
                            session.add(discovery_activity)

                            job.new_leads += 1
                            new_in_batch += 1

                    job.total_discovered += len(batch_leads)
                    job.total_processed += len(batch_leads)
                    total_scope_leads = (job.existing_businesses or 0) + job.new_leads
                    remaining_count = max(0, target_count - total_scope_leads)

                    if target_count > 0:
                        job.progress_percent = min(
                            100, int((total_scope_leads / target_count) * 100)
                        )

                    await session.commit()

                    if remaining_count <= 0:
                        break

                job.progress_percent = 100
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                await session.commit()

            except Exception as e:
                logger.error(f"Error executing discovery job {job_id}: {e}", exc_info=True)
                job.status = JobStatus.FAILED
                job.error_message = str(e)[:500]
                job.completed_at = datetime.now(UTC)
                await session.commit()
