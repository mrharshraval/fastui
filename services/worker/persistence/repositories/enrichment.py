"""
FastUI Enrichment Persistence Repository
========================================
Encapsulates database operations, transaction boundaries, and enriched profile
persistence for website analysis workflows.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.enrichment import EnrichedBusinessProfile
from domain.normalization import normalize_website
from persistence.models import (
    Activity,
    ActivityType,
    Business,
    CrawledWebsite,
    ProspectDemo,
)
from shared.phone import normalize_global_phone

logger = logging.getLogger("fastui.persistence.enrichment")


def compute_location_signature(address: Optional[str], city: Optional[str]) -> str:
    """Computes a deterministic hash for deduplicating crawl branches by physical location."""
    clean = f"{city or ''}:{address or ''}".lower().strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]


class EnrichmentRepository:
    """Repository handling database queries and persistence for website enrichment."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_business(self, business_id: int) -> Optional[Business]:
        """Retrieves a business by primary key."""
        return await self.session.get(Business, business_id)

    async def save_enrichment_result(
        self,
        business_id: int,
        profile: EnrichedBusinessProfile,
    ) -> CrawledWebsite:
        """
        Persists website extraction profile, updates business contact information,
        and generates or refreshes demo records.
        """
        biz = await self.get_business(business_id)
        if not biz:
            raise ValueError(f"Business with id {business_id} does not exist.")

        norm_domain = normalize_website(profile.website_url) or urlparse(profile.website_url).netloc
        loc_sig = compute_location_signature(biz.address, biz.city)

        # 1. Update or create CrawledWebsite
        stmt = select(CrawledWebsite).where(
            CrawledWebsite.business_id == business_id,
            CrawledWebsite.domain == norm_domain,
        )
        res = await self.session.execute(stmt)
        crawled = res.scalars().first()

        branches_data = [b.model_dump() for b in profile.branches] if profile.branches else None
        extracted_dump = profile.model_dump()

        if crawled:
            crawled.extracted_data = extracted_dump
            crawled.canonical_url = profile.canonical_url or profile.website_url
            crawled.branches = branches_data
            crawled.updated_at = datetime.now(timezone.utc)
        else:
            crawled = CrawledWebsite(
                domain=norm_domain,
                location_signature=loc_sig,
                business_id=business_id,
                canonical_url=profile.canonical_url or profile.website_url,
                branches=branches_data,
                extracted_data=extracted_dump,
                confidence_score=1.0,
            )
            self.session.add(crawled)

        # 2. Enrich business entity with high-confidence website signals
        if profile.brand and profile.brand.brand_name and len(profile.brand.brand_name) > 2:
            biz.canonical_name = profile.brand.brand_name

        if profile.contact:
            if not biz.email and profile.contact.emails:
                biz.email = profile.contact.emails[0]
            if not biz.phone and profile.contact.phones:
                disp, e164 = normalize_global_phone(profile.contact.phones[0], location=biz.city)
                biz.phone = disp or profile.contact.phones[0]
                biz.normalized_phone = e164
            if profile.contact.whatsapp or profile.contact.whatsapp_url:
                biz.has_whatsapp = True

        # 3. Create or update ProspectDemo
        demo_stmt = select(ProspectDemo).where(ProspectDemo.business_id == business_id)
        demo_res = await self.session.execute(demo_stmt)
        demo = demo_res.scalars().first()

        demo_overrides = {
            "hero_title": profile.tagline or f"Welcome to {biz.canonical_name}",
            "primary_color": (profile.brand.brand_colors or {}).get("primary"),
            "logo_url": profile.brand.logo_url,
            "doctor_name": profile.primary_doctor.name if profile.primary_doctor else None,
        }

        if demo:
            demo.custom_overrides = demo_overrides
            demo.updated_at = datetime.now(timezone.utc)
        else:
            token = hashlib.sha256(f"{business_id}:{norm_domain}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:32]
            demo = ProspectDemo(
                business_id=business_id,
                token=token,
                status="active",
                template_id="dental-default",
                custom_overrides=demo_overrides,
            )
            self.session.add(demo)

        # 4. Record Activity
        activity = Activity(
            business_id=business_id,
            type=ActivityType.WEBSITE_VISITED,
            channel="enrichment_crawler",
            outcome="enriched",
            notes=f"Enriched {len(profile.pages_crawled)} pages from {norm_domain}",
            entity_type="business",
            entity_id=business_id,
        )
        self.session.add(activity)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return crawled

    async def record_enrichment_failure(self, business_id: int, error_message: str) -> None:
        """Records an enrichment failure activity in the database.

        If the business no longer exists (e.g. deleted between task enqueue and
        processing, or a stale stream message), the activity insert is skipped and
        the failure is logged at WARNING level. Inserting an Activity against a
        non-existent business would violate the FK constraint and mask the real error.
        """
        biz = await self.get_business(business_id)
        if not biz:
            logger.warning(
                f"Skipping enrichment failure activity for business_id={business_id}: "
                "business does not exist in the database. The enrichment task is stale "
                "or the business was deleted after the task was enqueued."
            )
            return

        activity = Activity(
            business_id=business_id,
            type=ActivityType.WEBSITE_VISITED,
            channel="enrichment_crawler",
            outcome="failed",
            notes=f"Enrichment failed: {error_message[:300]}",
            entity_type="business",
            entity_id=business_id,
        )
        self.session.add(activity)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

