"""
FastUI Discovery & Lead Prospecting Service
===========================================
Orchestrates background scraping jobs, entity normalization, deduplication, and database persistence.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import settings
from core.exceptions import ConflictError, EntityNotFoundError
from models.database import AsyncSessionLocal
from models.schema import (
    Activity,
    ActivityType,
    Business,
    DiscoveryJob,
    JobStatus,
    WebsiteStatus,
)
from worker.contracts import DiscoverySearchParams
from worker.deduplication import LeadDeduplicator
from worker.normalizers import BusinessNameNormalizer
from worker.sources.aggregator import MultiSourceDiscoveryAggregator

logger = logging.getLogger(__name__)

# Concurrency semaphore preventing memory exhaustion from headless browsers
SCRAPER_SEMAPHORE = asyncio.Semaphore(settings.MAX_CONCURRENT_SCRAPERS)


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


def _run_scraper_in_worker_thread(params: DiscoverySearchParams) -> List[Any]:
    """Runs multi-source discovery in a dedicated worker thread with an isolated event loop."""
    import sys

    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        scraper = MultiSourceDiscoveryAggregator(headless=True)
        return loop.run_until_complete(scraper.discover(params))
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        except Exception:
            pass


class DiscoveryService:
    """
    Manages discovery job lifecycle, cancellation, and background extraction processing.
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
            raise ConflictError(f"Job {job_id} cannot be cancelled because it is already {job.status.value}")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(job)
        logger.info(f"Discovery job {job_id} marked as CANCELLED.")
        return job

    @staticmethod
    async def process_job(job_id: int) -> None:
        """
        Orchestrates scraping, normalization, deduplication, and persistence for a discovery job.
        """
        async with SCRAPER_SEMAPHORE:
            async with AsyncSessionLocal() as session:
                job = await session.get(DiscoveryJob, job_id)
                if not job or job.status != JobStatus.QUEUED:
                    return

                try:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now(timezone.utc)
                    await session.commit()

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

                    logger.info(f"Job {job_id}: Starting discovery for '{search_params.target_audience}' in '{search_params.location}'")
                    raw_leads = await asyncio.to_thread(_run_scraper_in_worker_thread, search_params)

                    # Check for mid-scrape cancellation
                    await session.refresh(job)
                    if job.status == JobStatus.CANCELLED:
                        logger.info(f"Job {job_id} was cancelled during extraction. Discarding results.")
                        return

                    job.total_discovered = len(raw_leads)

                    # Resolve location fields
                    loc_city = None
                    loc_state = None
                    loc_country = None
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

                    for i, lead in enumerate(raw_leads):
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
                                source_platform=lead.source_platform or "discover",
                            )
                            session.add(new_business)
                            await session.flush()

                            discovery_activity = Activity(
                                business_id=new_business.id,
                                type=ActivityType.BUSINESS_DISCOVERED,
                                channel="scraper",
                                outcome="Discovered via MultiSource Scraper",
                                notes=f"Discovered in '{location_str}' under '{target_audience}'",
                                entity_type="business",
                                entity_id=new_business.id,
                            )
                            session.add(discovery_activity)
                            job.new_leads += 1

                        job.total_processed += 1
                        job.progress_percent = int(((i + 1) / len(raw_leads)) * 100) if raw_leads else 100
                        await session.flush()

                    job.status = JobStatus.COMPLETED

                except Exception as e:
                    logger.error(f"Job {job_id} encountered fatal error: {e}", exc_info=True)
                    job.status = JobStatus.FAILED
                    job.error_message = str(e)

                finally:
                    job.completed_at = datetime.now(timezone.utc)
                    if job.status == JobStatus.COMPLETED:
                        job.progress_percent = 100
                    await session.commit()
                    logger.info(f"Job {job_id} completed with status: {job.status}")
