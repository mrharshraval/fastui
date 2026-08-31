"""
FastUI Discovery & Lead Prospecting Service
===========================================
Orchestrates discovery jobs by dispatching scraping work to the Cloud Run Worker
over authenticated HTTPS in bounded batches, then persists the results via
authoritative database deduplication and normalization.

Separation of concerns:
  DiscoveryJob     — owns target, progress, and remaining count
  DiscoveryService — orchestrates bounded batching, DB deduplication, and persistence
  WorkerClient     — handles authenticated transport to Cloud Run Worker
"""

import gc
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, select

from core.exceptions import ConflictError, EntityNotFoundError
from models.database import AsyncSessionLocal
from models.schema import (
    Activity,
    ActivityType,
    Business,
    BusinessSource,
    DiscoveryJob,
    JobStatus,
    WebsiteStatus,
)
from schemas.discovery import DiscoverySearchParams
from services.business_name_normalizer import BusinessNameNormalizer
from services.deduplication import LeadDeduplicator
from services.worker_client import WorkerClient

logger = logging.getLogger(__name__)

# Default bounded batch size to ensure peak memory never holds large sets
DEFAULT_BATCH_SIZE = 50
MAX_EMPTY_OR_DUPLICATE_BATCHES = 3


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


async def count_existing_prospects_for_scope(
    session, category: str, city: Optional[str]
) -> int:
    """
    Counts unique existing businesses matching the category and location scope.
    """
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


class DiscoveryService:
    """
    Manages discovery job lifecycle, bounded multi-source batching, and incremental persistence.
    """

    @staticmethod
    async def cancel_job(session, job_id: int) -> DiscoveryJob:
        """
        Cancels a queued or currently running discovery job.
        """
        job = await session.get(DiscoveryJob, job_id)
        if not job:
            raise EntityNotFoundError("DiscoveryJob", job_id)

        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            raise ConflictError(f"Job {job_id} cannot be cancelled — already {job.status.value}")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(job)
        logger.info(f"Discovery job {job_id} marked as CANCELLED.")
        return job

    @staticmethod
    async def process_job(job_id: int) -> None:
        """
        Dispatches bounded batches to the Cloud Run Worker, normalizes and deduplicates
        leads against the DB, and incrementally persists newly discovered prospects.
        """
        async with AsyncSessionLocal() as session:
            job = await session.get(DiscoveryJob, job_id)
            if not job or job.status != JobStatus.QUEUED:
                return

            try:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)
                await session.commit()

                # 1. Parse target query parameters
                query_dict = job.query if isinstance(job.query, dict) else {}
                loc_raw = query_dict.get("location") or query_dict.get("locations")
                location_str = build_location_string(loc_raw) or "Global"
                target_audience = (
                    query_dict.get("target_audience")
                    or query_dict.get("business_type")
                    or "Businesses"
                )
                target_count = int(
                    query_dict.get("target_count")
                    or query_dict.get("limit")
                    or 1000
                )

                # Resolve location components
                loc_city: Optional[str] = None
                loc_state: Optional[str] = None
                loc_country: Optional[str] = None
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

                # 2. Calculate existing unique prospects for this scope
                existing_unique = await count_existing_prospects_for_scope(
                    session, target_audience, loc_city
                )
                job.existing_businesses = existing_unique
                await session.commit()

                # 3. Calculate remaining count
                remaining_count = max(0, target_count - existing_unique)
                logger.info(
                    f"Job {job_id}: target={target_count}, existing={existing_unique}, "
                    f"remaining={remaining_count} for '{target_audience}' in '{location_str}'"
                )

                # If target is already satisfied by existing DB records, complete immediately
                if remaining_count <= 0:
                    logger.info(
                        f"Job {job_id}: Target {target_count} already satisfied by {existing_unique} "
                        f"existing prospects. Completing job without scraper calls."
                    )
                    job.progress_percent = 100
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return

                # 4. Bounded multi-source batching loop
                consecutive_non_productive_batches = 0

                while remaining_count > 0:
                    # Check for mid-run cancellation
                    await session.refresh(job)
                    if job.status == JobStatus.CANCELLED:
                        logger.info(f"Job {job_id} was cancelled. Stopping discovery loop.")
                        return

                    # Compute batch limit
                    batch_limit = min(DEFAULT_BATCH_SIZE, remaining_count)
                    search_params = DiscoverySearchParams(
                        target_audience=target_audience,
                        location=location_str,
                        limit=batch_limit,
                        batch_size=batch_limit,
                    )

                    logger.info(
                        f"Job {job_id}: Requesting batch of {batch_limit} leads (remaining={remaining_count})..."
                    )

                    # Call Worker
                    worker_response = await WorkerClient.discover_batch(search_params)
                    batch_leads = worker_response.leads

                    if not batch_leads:
                        logger.info(f"Job {job_id}: Worker returned 0 leads. Sources exhausted.")
                        break

                    new_in_batch = 0
                    dups_in_batch = 0

                    # 5. Authoritative normalization, deduplication & incremental persistence
                    for lead in batch_leads:
                        name_norm = BusinessNameNormalizer.normalize(lead.name)
                        norm_phone = LeadDeduplicator.normalize_phone(lead.phone)
                        norm_web = LeadDeduplicator.normalize_website(lead.website)

                        existing_biz = await LeadDeduplicator.find_duplicate(
                            session,
                            normalized_phone=norm_phone,
                            normalized_website=norm_web,
                            business_name=name_norm.display_name,
                            city=loc_city or lead.city,
                            source_platform=lead.source_platform,
                            source_place_id=lead.source_place_id,
                        )

                        if existing_biz:
                            job.duplicates += 1
                            dups_in_batch += 1

                            # Provenance & signal enrichment on existing business
                            if not existing_biz.phone and lead.phone:
                                existing_biz.phone = lead.phone
                                existing_biz.normalized_phone = norm_phone
                            if not existing_biz.website and lead.website:
                                existing_biz.website = lead.website
                                existing_biz.normalized_website = norm_web
                            if not existing_biz.email and lead.email:
                                existing_biz.email = lead.email
                        else:
                            web_status = (
                                WebsiteStatus.WEBSITE_FOUND
                                if lead.website
                                else WebsiteStatus.NO_WEBSITE
                            )
                            new_business = Business(
                                business_name=name_norm.display_name,
                                raw_business_name=name_norm.raw_name,
                                normalized_business_name=name_norm.normalized_name,
                                category=lead.category or target_audience,
                                address=getattr(lead, "address", None) or location_str,
                                city=loc_city or getattr(lead, "city", None) or location_str,
                                state=loc_state or getattr(lead, "state", None),
                                country=loc_country or getattr(lead, "country", None),
                                phone=lead.phone,
                                email=lead.email,
                                website=lead.website,
                                normalized_phone=norm_phone,
                                normalized_website=norm_web,
                                has_whatsapp=bool(lead.phone),
                                website_status=web_status,
                                qualification_status="unqualified",
                                source_platform=lead.source_platform or "google_maps",
                            )
                            session.add(new_business)
                            await session.flush()

                            # Persist business source provenance with external ID
                            business_source = BusinessSource(
                                business_id=new_business.id,
                                discovery_job_id=job.id,
                                platform=lead.source_platform or "google_maps",
                                source_url=lead.source_url,
                                external_id=lead.source_place_id,
                            )
                            session.add(business_source)

                            # Record discovery audit activity
                            discovery_activity = Activity(
                                business_id=new_business.id,
                                type=ActivityType.BUSINESS_DISCOVERED,
                                channel="scraper",
                                outcome=f"Discovered via {lead.source_platform or 'MultiSource'}",
                                notes=f"Discovered in '{location_str}' under '{target_audience}'",
                                entity_type="business",
                                entity_id=new_business.id,
                            )
                            session.add(discovery_activity)

                            job.new_leads += 1
                            new_in_batch += 1

                        job.total_processed += 1

                    job.total_discovered += len(batch_leads)

                    # Update remaining count and progress
                    total_scope_leads = job.existing_businesses + job.new_leads
                    remaining_count = max(0, target_count - total_scope_leads)
                    job.progress_percent = min(100, int((total_scope_leads / target_count) * 100))

                    # Incremental database commit
                    await session.commit()

                    logger.info(
                        f"Job {job_id} batch complete: +{new_in_batch} new, +{dups_in_batch} dups. "
                        f"Progress: {total_scope_leads}/{target_count} ({job.progress_percent}%), remaining={remaining_count}"
                    )

                    # Release batch memory
                    del batch_leads
                    del worker_response
                    gc.collect()

                    if new_in_batch == 0:
                        consecutive_non_productive_batches += 1
                        if consecutive_non_productive_batches >= MAX_EMPTY_OR_DUPLICATE_BATCHES:
                            logger.info(
                                f"Job {job_id}: {MAX_EMPTY_OR_DUPLICATE_BATCHES} consecutive batches produced 0 new leads. "
                                f"Treating sources as exhausted."
                            )
                            break
                    else:
                        consecutive_non_productive_batches = 0

                job.status = JobStatus.COMPLETED

            except Exception as e:
                logger.error(f"Job {job_id} encountered fatal error: {e}", exc_info=True)
                job.status = JobStatus.FAILED
                job.error_message = str(e)

            finally:
                job.completed_at = datetime.now(timezone.utc)
                if job.status == JobStatus.COMPLETED:
                    total_achieved = (job.existing_businesses or 0) + (job.new_leads or 0)
                    t_count = int(
                        (job.query or {}).get("target_count")
                        or (job.query or {}).get("limit")
                        or 1000
                    )
                    job.progress_percent = min(100, int((total_achieved / t_count) * 100)) if t_count > 0 else 100

                await session.commit()
                logger.info(
                    f"Job {job_id} finished: status={job.status.value}, "
                    f"new={job.new_leads}, existing={job.existing_businesses}, "
                    f"duplicates={job.duplicates}, progress={job.progress_percent}%"
                )
