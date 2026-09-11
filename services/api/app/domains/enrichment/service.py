"""FastUI Enrichment Domain Service.

Orchestrates asynchronous website enrichment via Cloud Run Worker, multi-factor
corroborated intelligence caching, and prospect personalization.
"""

import logging
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.businesses.deduplication import LeadDeduplicator
from app.domains.businesses.models import Business, BusinessSource
from app.domains.businesses.normalizer import BusinessNameNormalizer
from app.domains.engagement.models import Activity, ActivityType
from app.domains.enrichment.models import CrawledWebsite
from app.domains.enrichment.schemas import (
    BusinessEnrichmentStatusResponse,
    EnrichedBusinessProfile,
)
from app.infrastructure.database.session import get_db_session
from app.infrastructure.external.worker_client import WorkerClient
from app.shared.exceptions import EntityNotFoundError
from app.shared.phone import get_whatsapp_url, is_mobile_phone

logger = logging.getLogger("fastui.enrichment")


class EnrichmentService:
    """Manages asynchronous background website enrichment for FastUI prospects."""

    @staticmethod
    async def enrich_business_background(business_id: int) -> None:
        """Background task: calls Worker enrichment engine, parses profile, and updates DB."""
        logger.info(f"Starting background enrichment for business_id={business_id}")

        async with get_db_session() as session:
            stmt = (
                select(Business)
                .where(Business.id == business_id)
                .options(
                    selectinload(Business.sources),
                    selectinload(Business.demos),
                )
            )
            res = await session.execute(stmt)
            business = res.scalars().first()

            if not business or not business.website:
                logger.info(f"Enrichment aborted or skipped for business_id={business_id}")
                return

            target_url = business.website.strip()
            if not target_url.startswith("http://") and not target_url.startswith("https://"):
                target_url = f"https://{target_url}"

            try:
                worker_resp = await WorkerClient.enrich_business(
                    website=target_url,
                    business_name=business.business_name,
                )

                if not worker_resp or not worker_resp.success or not worker_resp.profile:
                    logger.warning(
                        f"Enrichment failed for business_id={business_id}: {worker_resp.error if worker_resp else 'No response'}"
                    )
                    failure_activity = Activity(
                        business_id=business.id,
                        type=ActivityType.WEBSITE_VISITED,
                        channel="enrichment_engine",
                        outcome="Enrichment Unsuccessful",
                        notes=f"Failed to enrich {target_url}: {worker_resp.error if worker_resp else 'No profile returned'}",
                        entity_type="business",
                        entity_id=business.id,
                        created_at=datetime.now(UTC),
                    )
                    session.add(failure_activity)
                    await session.commit()
                    return

                profile = EnrichedBusinessProfile.model_validate(worker_resp.profile)
                profile_dict = profile.model_dump()

                # 1. Update or create CrawledWebsite
                norm_domain = LeadDeduplicator.normalize_website(target_url)
                if norm_domain:
                    loc_sig = EnrichmentService.compute_location_signature(
                        business.address, business.city, business.postal_code
                    )
                    branch_payload = (
                        [b.model_dump() for b in profile.branches] if profile.branches else []
                    )
                    crawled_entry = CrawledWebsite(
                        domain=norm_domain,
                        location_signature=loc_sig,
                        business_id=business.id,
                        canonical_url=profile.canonical_url or target_url,
                        branches=branch_payload,
                        extracted_data=profile_dict,
                        confidence_score=1.0,
                    )
                    session.add(crawled_entry)

                # 2. Update BusinessSource
                website_source = None
                for src in business.sources:
                    if src.platform == "website":
                        website_source = src
                        break

                if website_source:
                    payload = dict(website_source.raw_payload or {})
                    payload["enrichment"] = profile_dict
                    website_source.raw_payload = payload
                    website_source.last_seen_at = datetime.now(UTC)
                    if profile.canonical_url:
                        website_source.source_url = profile.canonical_url
                else:
                    new_src = BusinessSource(
                        business_id=business.id,
                        platform="website",
                        source_url=profile.canonical_url or target_url,
                        external_id=f"{profile.canonical_url or target_url}#{business.id}",
                        raw_payload={"enrichment": profile_dict},
                    )
                    session.add(new_src)

                for src in business.sources:
                    if src.platform == "google_maps":
                        g_payload = dict(src.raw_payload or {})
                        g_payload["enrichment"] = profile_dict
                        src.raw_payload = g_payload

                # 3. Backfill missing Business core fields
                if not business.email and profile.contact.emails:
                    business.email = profile.contact.emails[0]
                if not business.has_whatsapp and profile.contact.whatsapp_url:
                    business.has_whatsapp = True
                if not business.phone and profile.contact.phone_numbers:
                    business.phone = profile.contact.phone_numbers[0]

                # 4. Synchronize active ProspectDemo custom_overrides
                for demo in business.demos:
                    demo.custom_overrides = EnrichmentService.personalize_demo_overrides(
                        prospect=business,
                        profile=profile,
                        existing_overrides=demo.custom_overrides,
                    )
                    demo.updated_at = datetime.now(UTC)

                # 5. Record Activity Log
                doctor_display = profile.primary_doctor.name if profile.primary_doctor else "None"
                quality_score = profile.quality.score if profile.quality else 0
                activity = Activity(
                    business_id=business.id,
                    type=ActivityType.WEBSITE_VISITED,
                    channel="enrichment_engine",
                    outcome=f"Enrichment Succeeded (Quality: {quality_score}/100)",
                    notes=(
                        f"Enriched brand (logo={'Yes' if profile.brand.logo_url else 'No'}), "
                        f"doctor ({doctor_display}), {len(profile.treatments)} specialties, "
                        f"tech ({profile.technology.cms or 'Custom'})."
                    ),
                    entity_type="business",
                    entity_id=business.id,
                    created_at=datetime.now(UTC),
                )
                session.add(activity)

                await session.commit()
                logger.info(
                    f"Background enrichment completed successfully for business_id={business_id}"
                )

            except Exception as e:
                logger.error(
                    f"Background enrichment error for business_id={business_id}: {e}", exc_info=True
                )
                await session.rollback()

    @staticmethod
    def extract_enrichment_from_business(business: Business) -> EnrichedBusinessProfile | None:
        """Helper to extract EnrichedBusinessProfile from any loaded BusinessSource."""
        if hasattr(business, "__dict__") and "sources" not in business.__dict__:
            return None
        sources = getattr(business, "sources", None)
        for source in sources or []:
            if source.raw_payload and isinstance(source.raw_payload, dict):
                enrichment_raw = source.raw_payload.get("enrichment")
                if enrichment_raw and isinstance(enrichment_raw, dict):
                    try:
                        return EnrichedBusinessProfile.model_validate(enrichment_raw)
                    except Exception as e:
                        logger.warning(f"Failed to validate cached enrichment payload: {e}")
        return None

    @staticmethod
    def compute_location_signature(
        address: str | None,
        city: str | None,
        postal_code: str | None,
    ) -> str:
        """Computes deterministic location signature for multi-branch disambiguation."""
        p_code = postal_code or LeadDeduplicator.extract_postal_code(address) or ""
        c_slug = re.sub(r"[^a-z0-9]", "", (city or "").lower())

        street_slug = ""
        if address:
            norm_addr = LeadDeduplicator.normalize_address(address)
            skip_words = {
                c_slug,
                p_code,
                "road",
                "street",
                "lane",
                "avenue",
                "near",
                "opp",
                "opposite",
                "beside",
                "floor",
                "shop",
                "no",
                "plot",
            }
            tokens = [w for w in norm_addr.split() if w not in skip_words]
            street_slug = "_".join(tokens[:3])

        parts = [p for p in (c_slug, p_code, street_slug) if p]
        return "_".join(parts) if parts else "default"

    @staticmethod
    async def find_matching_cached_intelligence(
        prospect: Business,
        normalized_domain: str,
        session: AsyncSession,
    ) -> CrawledWebsite | None:
        """Performs corroborated multi-factor matching against candidate cached records for the same domain.
        Never merges or reuses based on domain alone.
        """
        stmt = (
            select(CrawledWebsite)
            .where(CrawledWebsite.domain == normalized_domain)
            .order_by(CrawledWebsite.created_at.desc())
        )
        res = await session.execute(stmt)
        candidates = res.scalars().all()
        if not candidates:
            return None

        prospect_phone = LeadDeduplicator.normalize_phone(prospect.phone)
        prospect_postal = prospect.postal_code or LeadDeduplicator.extract_postal_code(
            prospect.address
        )
        prospect_loc_sig = EnrichmentService.compute_location_signature(
            prospect.address, prospect.city, prospect.postal_code
        )

        best_candidate: CrawledWebsite | None = None
        best_score = 0.0

        for candidate in candidates:
            score = 0.0
            cached_data = candidate.extracted_data or {}
            contact_data = cached_data.get("contact") or {}
            cached_phones = [
                LeadDeduplicator.normalize_phone(p)
                for p in contact_data.get("phone_numbers", [])
                if p
            ]
            cached_branches = candidate.branches or []

            # 1. Phone matching: direct corroborated match
            phone_matched = False
            if prospect_phone:
                if prospect_phone in cached_phones:
                    phone_matched = True
                    score += 0.95
                else:
                    for b in cached_branches:
                        if (
                            b.get("phone")
                            and LeadDeduplicator.normalize_phone(b["phone"]) == prospect_phone
                        ):
                            phone_matched = True
                            score += 0.95
                            break

            # 2. Exact location signature match
            if (
                candidate.location_signature
                and candidate.location_signature == prospect_loc_sig
                and prospect_loc_sig != "default"
            ):
                score += 0.90

            # 3. Address matching via LeadDeduplicator
            cached_addr = contact_data.get("address")
            cached_postal = LeadDeduplicator.extract_postal_code(cached_addr)

            if (
                prospect_postal
                and cached_postal
                and prospect_postal != cached_postal
                and not phone_matched
            ):
                branch_has_postal = any(
                    b.get("address")
                    and LeadDeduplicator.extract_postal_code(b["address"]) == prospect_postal
                    for b in cached_branches
                )
                if not branch_has_postal:
                    continue

            if prospect.city and cached_addr:
                prospect_city_clean = prospect.city.strip().lower()
                if prospect_city_clean not in cached_addr.lower() and not phone_matched:
                    branch_has_city = any(
                        b.get("address") and prospect_city_clean in b["address"].lower()
                        for b in cached_branches
                    )
                    if not branch_has_city:
                        continue

            addr_match = LeadDeduplicator.are_addresses_matching(
                prospect.address,
                cached_addr,
                postal1=prospect_postal,
                postal2=cached_postal,
                city=prospect.city,
            )
            if addr_match is True:
                score += 0.85
            elif not addr_match:
                for b in cached_branches:
                    b_addr = b.get("address")
                    if b_addr:
                        b_postal = LeadDeduplicator.extract_postal_code(b_addr)
                        if (
                            LeadDeduplicator.are_addresses_matching(
                                prospect.address,
                                b_addr,
                                postal1=prospect_postal,
                                postal2=b_postal,
                                city=prospect.city,
                            )
                            is True
                        ):
                            score += 0.85
                            break

            cached_brand = cached_data.get("brand", {})
            cached_name = cached_brand.get("brand_name") or cached_brand.get("name")
            if cached_name and prospect.business_name:
                if cached_name.lower().strip() == prospect.business_name.lower().strip():
                    score += 0.30

            if score > best_score and score >= 0.70:
                best_score = score
                best_candidate = candidate

        return best_candidate

    @staticmethod
    async def get_or_enrich_website(
        prospect: Business,
        session: AsyncSession,
        force_refresh: bool = False,
    ) -> tuple[EnrichedBusinessProfile | None, bool]:
        """High-level orchestrated retrieval for Create Demo flow:
        - Checks candidate cached website intelligence with corroborated validation.
        - Reuses cached data if matched.
        - Crawls and enriches fresh data if uncorroborated or uncached.
        """
        if not prospect.website:
            cached_profile = EnrichmentService.extract_enrichment_from_business(prospect)
            return (cached_profile, True if cached_profile else False)

        norm_domain = LeadDeduplicator.normalize_website(prospect.website)
        if not norm_domain:
            return (None, False)

        if not force_refresh:
            cached_record = await EnrichmentService.find_matching_cached_intelligence(
                prospect=prospect,
                normalized_domain=norm_domain,
                session=session,
            )
            if cached_record and cached_record.extracted_data:
                try:
                    profile = EnrichedBusinessProfile.model_validate(cached_record.extracted_data)
                    brand_name = getattr(profile.brand, "brand_name", None) or getattr(
                        profile.brand, "name", None
                    )
                    meta_title = getattr(profile.brand, "meta_title", None)
                    resolved_name = BusinessNameNormalizer.resolve_canonical_name(
                        source_name=getattr(prospect, "source_name", None)
                        or getattr(prospect, "raw_business_name", None)
                        or prospect.business_name,
                        website_brand=brand_name,
                        website_title=meta_title,
                    )
                    if resolved_name.display_name:
                        prospect.canonical_name = resolved_name.display_name
                        prospect.business_name = resolved_name.display_name

                    if not prospect.email and profile.contact.emails:
                        prospect.email = profile.contact.emails[0]
                    if not prospect.has_whatsapp and (
                        profile.contact.whatsapp_url or profile.contact.whatsapp
                    ):
                        prospect.has_whatsapp = True
                    if not prospect.phone and (
                        profile.contact.phone_numbers or profile.contact.phones
                    ):
                        phone_cand = (profile.contact.phone_numbers or profile.contact.phones)[0]
                        prospect.phone = phone_cand
                        if is_mobile_phone(phone_cand, location=prospect.city):
                            prospect.has_whatsapp = True
                    await session.commit()

                    logger.info(
                        f"Corroborated cache hit for domain '{norm_domain}' "
                        f"(crawled_id={cached_record.id}, business_id={prospect.id})"
                    )
                    return (profile, True)
                except Exception as e:
                    logger.warning(f"Failed to parse cached CrawledWebsite data: {e}")

        target_url = prospect.website.strip()
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = f"https://{target_url}"

        logger.info(
            f"Initiating fresh website crawl for '{target_url}' (prospect_id={prospect.id})"
        )
        try:
            enrich_resp = await WorkerClient.enrich_business(
                website=target_url,
                business_name=prospect.business_name,
            )
            if not enrich_resp or not enrich_resp.success or not enrich_resp.profile:
                logger.warning(f"Enrichment returned unsuccessful for {target_url}")
                return (None, False)

            profile = EnrichedBusinessProfile.model_validate(enrich_resp.profile)
            profile_dict = profile.model_dump()

            loc_sig = EnrichmentService.compute_location_signature(
                prospect.address,
                prospect.city,
                prospect.postal_code,
            )
            branch_payload = [b.model_dump() for b in profile.branches] if profile.branches else []
            crawled_entry = CrawledWebsite(
                domain=norm_domain,
                location_signature=loc_sig,
                business_id=prospect.id,
                canonical_url=profile.canonical_url or target_url,
                branches=branch_payload,
                extracted_data=profile_dict,
                confidence_score=1.0,
            )
            session.add(crawled_entry)

            stmt_sources = select(BusinessSource).where(BusinessSource.business_id == prospect.id)
            res_sources = await session.execute(stmt_sources)
            existing_sources = res_sources.scalars().all()

            website_source = next((s for s in existing_sources if s.platform == "website"), None)
            if website_source:
                payload = dict(website_source.raw_payload or {})
                payload["enrichment"] = profile_dict
                website_source.raw_payload = payload
                website_source.last_seen_at = datetime.now(UTC)
            else:
                new_src = BusinessSource(
                    business_id=prospect.id,
                    platform="website",
                    source_url=profile.canonical_url or target_url,
                    external_id=f"{profile.canonical_url or target_url}#{prospect.id}",
                    raw_payload={"enrichment": profile_dict},
                )
                session.add(new_src)

            for src in existing_sources:
                if src.platform == "google_maps":
                    g_payload = dict(src.raw_payload or {})
                    g_payload["enrichment"] = profile_dict
                    src.raw_payload = g_payload

            brand_name = getattr(profile.brand, "brand_name", None) or getattr(
                profile.brand, "name", None
            )
            meta_title = getattr(profile.brand, "meta_title", None)
            resolved_name = BusinessNameNormalizer.resolve_canonical_name(
                source_name=getattr(prospect, "source_name", None)
                or getattr(prospect, "raw_business_name", None)
                or prospect.business_name,
                website_brand=brand_name,
                website_title=meta_title,
            )
            if resolved_name.display_name:
                prospect.canonical_name = resolved_name.display_name
                prospect.business_name = resolved_name.display_name

            if not prospect.email and profile.contact.emails:
                prospect.email = profile.contact.emails[0]
            if not prospect.has_whatsapp and (
                profile.contact.whatsapp_url or profile.contact.whatsapp
            ):
                prospect.has_whatsapp = True
            if not prospect.phone and (profile.contact.phone_numbers or profile.contact.phones):
                phone_cand = (profile.contact.phone_numbers or profile.contact.phones)[0]
                prospect.phone = phone_cand
                if is_mobile_phone(phone_cand, location=prospect.city):
                    prospect.has_whatsapp = True

            await session.commit()
            return (profile, False)

        except Exception as e:
            logger.error(f"Failed to crawl/enrich website {target_url}: {e}", exc_info=True)
            return (None, False)

    @staticmethod
    async def get_business_enrichment_status(
        session: AsyncSession, business_id: int
    ) -> BusinessEnrichmentStatusResponse:
        """Fetches the enriched profile and quality audit results for a business."""
        stmt = (
            select(Business)
            .where(Business.id == business_id)
            .options(selectinload(Business.sources))
            .execution_options(populate_existing=True)
        )
        res = await session.execute(stmt)
        business = res.scalars().first()

        if not business:
            raise EntityNotFoundError("Business", business_id)

        profile = EnrichmentService.extract_enrichment_from_business(business)
        if not profile:
            return BusinessEnrichmentStatusResponse(
                business_id=business.id,
                is_enriched=False,
                treatments_count=0,
            )

        return BusinessEnrichmentStatusResponse(
            business_id=business.id,
            is_enriched=True,
            enriched_at=profile.extracted_at,
            quality_score=profile.quality.score if profile.quality else None,
            brand=profile.brand,
            primary_doctor=profile.primary_doctor,
            treatments_count=len(profile.treatments),
            profile=profile,
        )

    @staticmethod
    def personalize_demo_overrides(
        prospect: Business,
        profile: EnrichedBusinessProfile | None,
        existing_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Creates personalized demo presentation overrides from corroborated website intelligence."""
        overrides = dict(existing_overrides or {})
        if not profile:
            return overrides

        canonical = getattr(prospect, "canonical_name", None) or getattr(
            prospect, "business_name", None
        )
        if canonical and not overrides.get("clinic_name"):
            overrides["clinic_name"] = canonical

        if profile.brand_colors:
            overrides["brand_colors"] = profile.brand_colors
        if profile.brand.logo_url and not overrides.get("logo_url"):
            overrides["logo_url"] = profile.brand.logo_url

        tagline = profile.tagline or profile.brand.tagline
        if tagline and not overrides.get("tagline"):
            overrides["tagline"] = tagline
            if (
                not overrides.get("hero_headline")
                or overrides.get("hero_headline") == "Where healthy smiles begin."
            ):
                overrides["hero_headline"] = tagline

        about = profile.about_text or profile.brand.about_text
        if about and not overrides.get("about_text"):
            overrides["about_text"] = about
            if (
                not overrides.get("hero_subheadline")
                or overrides.get("hero_subheadline")
                == "Comprehensive, gentle dental care tailored to your family's needs."
            ):
                overrides["hero_subheadline"] = about[:140] + ("..." if len(about) > 140 else "")

        if profile.primary_doctor:
            doc = profile.primary_doctor
            if doc.name and not overrides.get("doctor_name"):
                overrides["doctor_name"] = doc.name
            if doc.title and not overrides.get("doctor_title"):
                overrides["doctor_title"] = doc.title
            if doc.bio and not overrides.get("doctor_bio"):
                overrides["doctor_bio"] = doc.bio
            if doc.photo_url and not overrides.get("doctor_photo_url"):
                overrides["doctor_photo_url"] = doc.photo_url

        if profile.doctors and not overrides.get("doctors"):
            overrides["doctors"] = [d.model_dump() for d in profile.doctors]

        if profile.treatments and not overrides.get("specialties"):
            top_treatments = [
                cat
                for cat, s in sorted(
                    profile.treatments.items(),
                    key=lambda item: item[1].confidence,
                    reverse=True,
                )
                if s.confidence >= 0.3
            ]
            if top_treatments:
                overrides["specialties"] = top_treatments

        if profile.testimonials and not overrides.get("testimonials"):
            overrides["testimonials"] = [t.model_dump() for t in profile.testimonials]

        if profile.faqs and not overrides.get("faqs"):
            overrides["faqs"] = [f.model_dump() for f in profile.faqs]

        if profile.facilities and not overrides.get("facilities"):
            overrides["facilities"] = profile.facilities

        if profile.certifications and not overrides.get("certifications"):
            overrides["certifications"] = profile.certifications

        if (
            profile.insurance_info
            and profile.insurance_info.get("providers")
            and not overrides.get("insurance_providers")
        ):
            overrides["insurance_providers"] = profile.insurance_info["providers"]

        if profile.emergency_services and not overrides.get("emergency_info"):
            overrides["emergency_info"] = profile.emergency_services

        booking = profile.contact.booking_url
        if booking and not overrides.get("booking_url"):
            overrides["booking_url"] = booking

        if profile.branches and not overrides.get("branches"):
            overrides["branches"] = [b.model_dump() for b in profile.branches]

        if profile.reusable_images and not overrides.get("reusable_images"):
            overrides["reusable_images"] = profile.reusable_images
            if (
                profile.reusable_images.get("hero")
                and overrides.get("hero_image_url") == "/hero_dentist_v1.webp"
            ):
                overrides["hero_image_url"] = profile.reusable_images["hero"][0]
            if (
                profile.reusable_images.get("clinic")
                and overrides.get("clinic_interior_url") == "/hero_dentist_v1.webp"
            ):
                overrides["clinic_interior_url"] = profile.reusable_images["clinic"][0]

        if profile.opening_hours and not overrides.get("opening_hours"):
            if isinstance(profile.opening_hours, dict):
                overrides["opening_hours_structured"] = profile.opening_hours
            else:
                overrides["opening_hours"] = str(profile.opening_hours)

        if profile.contact and profile.contact.social_links and not overrides.get("social_links"):
            overrides["social_links"] = dict(profile.contact.social_links)

        wa_url = (
            profile.contact.whatsapp_url or profile.contact.whatsapp if profile.contact else None
        )
        if not wa_url and prospect.phone:
            if prospect.has_whatsapp or is_mobile_phone(prospect.phone, location=prospect.city):
                wa_url = get_whatsapp_url(prospect.phone, location=prospect.city)

        if wa_url and not overrides.get("whatsapp_url"):
            overrides["whatsapp_url"] = wa_url

        return overrides
