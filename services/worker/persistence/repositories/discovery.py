"""
FastUI Discovery Persistence Repository
=======================================
Encapsulates all database operations, transaction boundaries, and deduplicated
lead persistence for discovery jobs and tasks.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple  # noqa: UP035

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.discovery import DiscoveredLead
from domain.identity import GENERIC_DOMAINS
from domain.normalization import normalize_address, normalize_business_name, normalize_website
from persistence.models import (
    Activity,
    ActivityType,
    Business,
    BusinessSource,
    DiscoveryJob,
    DiscoveryTask,
    JobStatus,
    TaskStatus,
    WebsiteStatus,
)
from shared.phone import normalize_global_phone

logger = logging.getLogger("fastui.persistence.discovery")


class DiscoveryRepository:
    """Repository handling database queries and entity resolution for discovery workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_task(self, task_id: int) -> Optional[DiscoveryTask]:
        """Retrieves a discovery task by primary key."""
        return await self.session.get(DiscoveryTask, task_id)

    async def get_job(self, job_id: int) -> Optional[DiscoveryJob]:
        """Retrieves a discovery job by primary key."""
        return await self.session.get(DiscoveryJob, job_id)

    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """Updates task execution status and optional error message."""
        try:
            task = await self.get_task(task_id)
            if task:
                task.status = status
                if error_message:
                    task.error_message = error_message[:1000]
                if status == TaskStatus.RUNNING:
                    task.attempts += 1
                await self.session.commit()
        except Exception as e:
            logger.error(f"Failed to update status for task {task_id}: {e}", exc_info=True)
            await self.session.rollback()
            raise

    async def create_continuation_task(
        self,
        job_id: int,
        params: Dict[str, Any],
    ) -> DiscoveryTask:
        """Persists a new paginated continuation task for a discovery job."""
        try:
            new_task = DiscoveryTask(
                job_id=job_id,
                status=TaskStatus.PENDING,
                params=params,
            )
            self.session.add(new_task)
            await self.session.commit()
            await self.session.refresh(new_task)
            return new_task
        except Exception as e:
            logger.error(f"Failed to create continuation task for job {job_id}: {e}", exc_info=True)
            await self.session.rollback()
            raise

    async def find_duplicate_business(self, lead: DiscoveredLead) -> Optional[Business]:
        """
        Database entity resolution using multi-attribute lookup.
        Never relies on business name alone.
        """
        # 1. Check Google Place ID / external ID
        place_id = lead.google_place_id or lead.source_place_id
        if place_id:
            stmt = select(Business).join(BusinessSource).where(BusinessSource.external_id == place_id)
            result = await self.session.execute(stmt)
            existing = result.scalars().first()
            if existing:
                return existing

        # 2. Check normalized phone
        _, e164 = normalize_global_phone(lead.phone, location=lead.city or lead.address)
        if e164:
            stmt = select(Business).where(Business.normalized_phone == e164)
            result = await self.session.execute(stmt)
            existing = result.scalars().first()
            if existing:
                return existing

        # 3. Check normalized website (excluding generic portals)
        norm_web = normalize_website(lead.website)
        if norm_web and norm_web not in GENERIC_DOMAINS:
            stmt = select(Business).where(Business.normalized_website == norm_web)
            result = await self.session.execute(stmt)
            existing = result.scalars().first()
            if existing:
                return existing

        # 4. Check normalized name co-located with same city or address
        norm_name = lead.normalized_name or normalize_business_name(lead.name).normalized_name
        if norm_name and (lead.city or lead.address):
            conditions = [Business.normalized_business_name == norm_name]
            if lead.city:
                conditions.append(func.lower(Business.city) == lead.city.lower())
            stmt = select(Business).where(and_(*conditions))
            result = await self.session.execute(stmt)
            candidates = result.scalars().all()
            for cand in candidates:
                if lead.address and cand.address:
                    clean_a = normalize_address(lead.address)
                    clean_b = normalize_address(cand.address)
                    if clean_a and clean_b and (clean_a == clean_b or clean_a in clean_b or clean_b in clean_a):
                        return cand

        return None

    async def persist_lead(
        self,
        job_id: int,
        lead: DiscoveredLead,
    ) -> Tuple[Business, bool]:
        """
        Idempotently persists or updates a discovered business lead.
        Returns a tuple of (business_record, is_new).
        """
        existing = await self.find_duplicate_business(lead)

        name_obj = normalize_business_name(lead.name)
        display_phone, e164 = normalize_global_phone(lead.phone, location=lead.city or lead.address)
        norm_web = normalize_website(lead.website)
        place_id = lead.google_place_id or lead.source_place_id

        if existing:
            # Update missing attributes on existing business record
            if not existing.phone and (display_phone or lead.phone):
                existing.phone = display_phone or lead.phone
                existing.normalized_phone = e164
            if not existing.website and lead.website:
                existing.website = lead.website
                existing.normalized_website = norm_web
                existing.website_status = WebsiteStatus.WEBSITE_FOUND
            if not existing.address and lead.address:
                existing.address = lead.address

            # Update or create source association — atomic upsert to prevent
            # duplicate-key races when multiple workers encounter the same place_id.
            if place_id:
                try:
                    stmt_upsert = (
                        pg_insert(BusinessSource)
                        .values(
                            business_id=existing.id,
                            discovery_job_id=job_id,
                            platform=lead.source_platform,
                            source_url=lead.source_url or lead.google_maps_url,
                            external_id=place_id,
                            raw_payload=lead.model_dump(),
                            last_seen_at=datetime.now(timezone.utc),
                            created_at=datetime.now(timezone.utc),
                        )
                        .on_conflict_do_update(
                            constraint="uq_business_source_platform_external_id",
                            set_={"last_seen_at": datetime.now(timezone.utc)},
                        )
                    )
                    await self.session.execute(stmt_upsert)
                except Exception:
                    # SQLite fallback (tests): check-then-insert
                    src_stmt = select(BusinessSource).where(
                        and_(
                            BusinessSource.business_id == existing.id,
                            BusinessSource.platform == lead.source_platform,
                        )
                    )
                    src_res = await self.session.execute(src_stmt)
                    source_rec = src_res.scalars().first()
                    if source_rec:
                        source_rec.last_seen_at = datetime.now(timezone.utc)
                    else:
                        self.session.add(BusinessSource(
                            business_id=existing.id,
                            discovery_job_id=job_id,
                            platform=lead.source_platform,
                            source_url=lead.source_url or lead.google_maps_url,
                            external_id=place_id,
                            raw_payload=lead.model_dump(),
                            last_seen_at=datetime.now(timezone.utc),
                            created_at=datetime.now(timezone.utc),
                        ))
            else:
                # No external ID — safe to do plain check-then-insert
                src_stmt = select(BusinessSource).where(
                    and_(
                        BusinessSource.business_id == existing.id,
                        BusinessSource.platform == lead.source_platform,
                    )
                )
                src_res = await self.session.execute(src_stmt)
                source_rec = src_res.scalars().first()
                if source_rec:
                    source_rec.last_seen_at = datetime.now(timezone.utc)
                else:
                    self.session.add(BusinessSource(
                        business_id=existing.id,
                        discovery_job_id=job_id,
                        platform=lead.source_platform,
                        source_url=lead.source_url or lead.google_maps_url,
                        external_id=place_id,
                        raw_payload=lead.model_dump(),
                        last_seen_at=datetime.now(timezone.utc),
                        created_at=datetime.now(timezone.utc),
                    ))

            # Touch updated_at so the business record reflects the new discovery pass
            existing.updated_at = datetime.now(timezone.utc)

            await self.session.flush()
            return existing, False

        # Create new business entity
        now = datetime.now(timezone.utc)
        new_business = Business(
            canonical_name=name_obj.display_name,
            source_name=lead.name,
            business_name=name_obj.display_name,
            raw_business_name=lead.raw_name or lead.name,
            normalized_business_name=name_obj.normalized_name,
            category=lead.category,
            address=lead.address,
            city=lead.city,
            state=lead.state,
            postal_code=lead.postal_code,
            country=lead.country,
            phone=display_phone or lead.phone,
            email=lead.email,
            website=lead.website,
            normalized_phone=e164,
            normalized_website=norm_web,
            has_whatsapp=lead.has_whatsapp,
            website_status=WebsiteStatus.WEBSITE_FOUND if lead.website else WebsiteStatus.NO_WEBSITE,
            qualification_status="unqualified",
            source_platform=lead.source_platform,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_business)
        await self.session.flush()

        # Add initial source record
        source_rec = BusinessSource(
            business_id=new_business.id,
            discovery_job_id=job_id,
            platform=lead.source_platform,
            source_url=lead.source_url or lead.google_maps_url,
            external_id=place_id,
            raw_payload=lead.model_dump(),
            last_seen_at=now,
            created_at=now,
        )
        self.session.add(source_rec)

        # Record activity
        activity = Activity(
            business_id=new_business.id,
            type=ActivityType.BUSINESS_DISCOVERED,
            channel=lead.source_platform,
            outcome="discovered",
            notes=f"Discovered via {lead.source_platform} during job {job_id}",
            entity_type="business",
            entity_id=new_business.id,
            created_at=now,
        )
        self.session.add(activity)
        await self.session.flush()

        return new_business, True

    async def persist_leads_batch(
        self,
        job_id: int,
        task_id: int,
        leads: List[DiscoveredLead],
    ) -> Tuple[int, int]:
        """
        Processes and commits a batch of discovered leads with transactional safety.
        Returns (new_leads_count, duplicates_count).

        Each lead is isolated in a savepoint so a single bad record cannot poison
        the session or misattribute failures to subsequent leads.
        Enrichment is an independent, explicitly triggered workflow; this method
        never enqueues enrichment tasks as a side effect.

        Leads are sorted deterministically by (source_platform, external_id, name)
        before processing so that concurrent transactions always acquire row locks
        in the same order, eliminating cyclic deadlocks (ShareLock / RowExclusiveLock).
        """
        # Deterministic lock order — prevents deadlocks under concurrent batch processing
        sorted_leads = sorted(
            leads,
            key=lambda l: (l.source_platform or "", l.source_place_id or l.google_place_id or "", l.name or ""),
        )

        new_count = 0
        dup_count = 0

        for lead in sorted_leads:
            try:
                async with self.session.begin_nested():
                    _biz, is_new = await self.persist_lead(job_id, lead)
                if is_new:
                    new_count += 1
                else:
                    dup_count += 1
            except Exception as e:
                logger.error(f"Failed to persist lead '{lead.name}': {e}", exc_info=True)
                continue

        try:
            await self.session.commit()
        except Exception as e:
            logger.error(f"Failed to commit batch for job {job_id}, task {task_id}: {e}", exc_info=True)
            await self.session.rollback()
            raise

        return new_count, dup_count

    async def update_job_progress(
        self,
        job_id: int,
        new_leads: int,
        duplicates: int,
        is_exhausted: bool = False,
    ) -> None:
        """Updates cumulative counters and completion metrics on DiscoveryJob."""
        try:
            job = await self.get_job(job_id)
            if not job:
                return

            job.total_discovered += (new_leads + duplicates)
            job.total_processed += (new_leads + duplicates)
            job.new_leads += new_leads
            job.duplicates += duplicates

            target = int((job.query or {}).get("target_count") or (job.query or {}).get("limit") or 1000)
            total_scope = (job.existing_businesses or 0) + job.new_leads
            job.progress_percent = min(100, int((total_scope / max(1, target)) * 100))

            if is_exhausted or total_scope >= target:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.progress_percent = 100

            await self.session.commit()
        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {e}", exc_info=True)
            await self.session.rollback()
            raise
