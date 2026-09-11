"""FastUI Demos Domain Service.

Manages interactive demo tokens, presentation schemas, visitor telemetry,
and real-time sales team alert broadcasts.
"""

import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import settings
from app.domains.businesses.models import Business
from app.domains.demos.models import DemoEvent, ProspectDemo
from app.domains.demos.schemas import (
    DemoCreateRequest,
    DemoEventCreate,
    DemoResponse,
    DentalBusinessPresentation,
    DentalCustomization,
    DentalDemoPresentation,
)
from app.domains.notifications.service import NotificationService
from app.infrastructure.database.session import get_db_session
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger("fastui.demos")

BOT_REGEX = re.compile(
    r"(bot|crawl|spider|slurp|facebookexternalhit|whatsapp|telegram|twitterbot|slackbot|discordbot|lighthouse|embedly|preview|headlesschrome)",
    re.IGNORECASE,
)


def is_bot(user_agent: str | None) -> bool:
    if not user_agent:
        return False
    return bool(BOT_REGEX.search(user_agent))


async def _dispatch_demo_event_push(business_id: int, business_name: str, event_type: str) -> None:
    """Dispatches background Web Push alert using an independent database session."""
    if event_type == "demo_viewed":
        push_title = "🔥 Prospect Viewed Demo!"
        push_body = f"{business_name} just opened their personalized website demo."
    elif event_type == "whatsapp_clicked":
        push_title = "💬 WhatsApp Clicked on Demo!"
        push_body = f"Prospect from {business_name} clicked the WhatsApp chat button!"
    elif event_type == "call_clicked":
        push_title = "📞 Call Clicked on Demo!"
        push_body = f"Prospect from {business_name} clicked to call the clinic!"
    else:
        push_title = "⚡ Prospect Engaged with Demo!"
        push_body = f"{business_name} took action: {event_type.replace('_', ' ').title()}"

    payload = {
        "title": push_title,
        "body": push_body,
        "icon": "/assets/brand/icon/monochrome/white/solid.png",
        "badge": "/assets/brand/notification/badge/monochrome/white/solid.png",
        "data": {
            "business_id": business_id,
            "url": f"/businesses/{business_id}",
            "event_type": event_type,
        },
    }

    try:
        async with get_db_session() as session:
            await NotificationService.broadcast_to_all_accounts(session=session, payload=payload)
    except Exception as e:
        logger.error(f"Failed to dispatch demo event push notification: {e}")


class DemoService:
    """Service managing business demos and public viewing interactions."""

    @staticmethod
    async def create_or_get_demo(
        session: AsyncSession,
        business_id: int,
        req: DemoCreateRequest | None = None,
        user_id: int | None = None,
    ) -> DemoResponse:
        business = await session.get(Business, business_id)
        if not business:
            raise EntityNotFoundError("Business", business_id)

        stmt = (
            select(ProspectDemo)
            .where(and_(ProspectDemo.business_id == business_id, ProspectDemo.status == "active"))
            .order_by(ProspectDemo.created_at.desc())
        )
        result = await session.execute(stmt)
        demo = result.scalars().first()

        profile = None
        if business.website:
            from app.domains.enrichment.service import EnrichmentService

            try:
                profile, _ = await EnrichmentService.get_or_enrich_website(
                    prospect=business,
                    session=session,
                )
            except Exception as e:
                logger.warning(f"Could not retrieve website enrichment for demo: {e}")

        base_overrides = req.custom_overrides if req and req.custom_overrides else {}
        if profile:
            from app.domains.enrichment.service import EnrichmentService

            merged_overrides = EnrichmentService.personalize_demo_overrides(
                prospect=business,
                profile=profile,
                existing_overrides=base_overrides,
            )
        else:
            merged_overrides = base_overrides or None

        if not demo:
            token = secrets.token_urlsafe(24)
            demo = ProspectDemo(
                business_id=business_id,
                token=token,
                status="active",
                template_id="dental-default",
                custom_overrides=merged_overrides,
                created_by_user_id=user_id,
            )
            session.add(demo)
            await session.commit()
            await session.refresh(demo)
        elif merged_overrides:
            existing = dict(demo.custom_overrides or {})
            existing.update(merged_overrides)
            demo.custom_overrides = existing
            await session.commit()
            await session.refresh(demo)

        base_url = settings.DEMO_BASE_URL.rstrip("/")
        demo_url = f"{base_url}/{demo.token}"

        return DemoResponse(
            id=demo.id,
            business_id=demo.business_id,
            token=demo.token,
            demo_url=demo_url,
            status=demo.status,
            template_id=demo.template_id,
            custom_overrides=demo.custom_overrides,
            view_count=demo.view_count,
            last_viewed_at=demo.last_viewed_at,
            created_at=demo.created_at,
            updated_at=demo.updated_at,
        )

    @staticmethod
    async def get_business_demo(session: AsyncSession, business_id: int) -> DemoResponse:
        stmt = (
            select(ProspectDemo)
            .where(and_(ProspectDemo.business_id == business_id, ProspectDemo.status == "active"))
            .order_by(ProspectDemo.created_at.desc())
        )
        result = await session.execute(stmt)
        demo = result.scalars().first()

        if not demo:
            raise EntityNotFoundError("Demo", business_id)

        base_url = settings.DEMO_BASE_URL.rstrip("/")
        demo_url = f"{base_url}/{demo.token}"

        return DemoResponse(
            id=demo.id,
            business_id=demo.business_id,
            token=demo.token,
            demo_url=demo_url,
            status=demo.status,
            template_id=demo.template_id,
            custom_overrides=demo.custom_overrides,
            view_count=demo.view_count,
            last_viewed_at=demo.last_viewed_at,
            created_at=demo.created_at,
            updated_at=demo.updated_at,
        )

    @staticmethod
    async def get_public_presentation(session: AsyncSession, token: str) -> DentalDemoPresentation:
        stmt = (
            select(ProspectDemo)
            .where(and_(ProspectDemo.token == token, ProspectDemo.status == "active"))
            .options(selectinload(ProspectDemo.business).selectinload(Business.sources))
        )
        result = await session.execute(stmt)
        demo = result.scalars().first()

        if not demo or not demo.business:
            raise EntityNotFoundError("Demo", token)

        business: Business = demo.business

        rating = 4.9
        reviews_count = 120
        place_id = None
        opening_hours = "Mon-Sat: 9:00 AM - 8:00 PM"

        for source in business.sources:
            if source.platform == "google_maps":
                if source.external_id:
                    place_id = source.external_id
                if source.raw_payload and isinstance(source.raw_payload, dict):
                    rating = float(source.raw_payload.get("rating") or rating)
                    reviews_count = int(source.raw_payload.get("reviews_count") or reviews_count)
                    if source.raw_payload.get("opening_hours"):
                        opening_hours = str(source.raw_payload.get("opening_hours"))
                break

        overrides = demo.custom_overrides or {}

        logo_url = overrides.get("logo_url")
        if not logo_url:
            for source in business.sources:
                if source.raw_payload and isinstance(source.raw_payload, dict):
                    enrichment = source.raw_payload.get("enrichment")
                    if isinstance(enrichment, dict):
                        brand = enrichment.get("brand") or {}
                        if brand.get("logo_url"):
                            logo_url = brand["logo_url"]
                            break
                    elif source.raw_payload.get("logo_url"):
                        logo_url = source.raw_payload.get("logo_url")
                        break

        if overrides.get("opening_hours"):
            opening_hours = str(overrides.get("opening_hours"))

        phone = business.phone or ""
        whatsapp = phone if business.has_whatsapp else (phone or None)
        social_links = overrides.get("social_links")
        whatsapp_url = overrides.get("whatsapp_url")
        if not whatsapp_url and whatsapp:
            clean_digits = re.sub(r"\D", "", whatsapp)
            if len(clean_digits) >= 10:
                whatsapp_url = f"https://wa.me/{clean_digits}"

        display_name = (
            overrides.get("clinic_name")
            or getattr(business, "canonical_name", None)
            or business.business_name
        )

        business_data = DentalBusinessPresentation(
            name=display_name,
            category=business.category or "Dental Clinic",
            phone=business.phone,
            email=business.email,
            whatsapp=whatsapp,
            whatsapp_url=whatsapp_url,
            social_links=social_links,
            address=business.address,
            city=business.city,
            state=business.state,
            country=business.country,
            postal_code=business.postal_code,
            opening_hours=opening_hours,
            rating=rating,
            reviews_count=reviews_count,
            place_id=place_id,
            website=business.website,
            logo_url=logo_url,
            branches=overrides.get("branches"),
        )
        customization = DentalCustomization(
            hero_headline=overrides.get("hero_headline", "Where healthy smiles begin."),
            hero_subheadline=overrides.get(
                "hero_subheadline",
                f"Comprehensive, gentle dental care tailored to your family's needs in {business.city or 'our community'}.",
            ),
            hero_image_url=overrides.get("hero_image_url", "/hero_dentist_v1.webp"),
            doctor_name=overrides.get("doctor_name", "Dr. Sarah Jenkins"),
            doctor_title=overrides.get("doctor_title", "Chief Dental Surgeon"),
            doctor_bio=overrides.get(
                "doctor_bio",
                "Specializing in cosmetic dentistry, dental implants, and compassionate preventive dental care.",
            ),
            doctor_photo_url=overrides.get("doctor_photo_url", "/female_dentist_portrait_1.png"),
            clinic_interior_url=overrides.get("clinic_interior_url", "/hero_dentist_v1.webp"),
            tagline=overrides.get("tagline"),
            about_text=overrides.get("about_text"),
            brand_colors=overrides.get("brand_colors"),
            doctors=overrides.get("doctors"),
            testimonials=overrides.get("testimonials"),
            faqs=overrides.get("faqs"),
            facilities=overrides.get("facilities"),
            certifications=overrides.get("certifications"),
            insurance_providers=overrides.get("insurance_providers"),
            emergency_info=overrides.get("emergency_info"),
            booking_url=overrides.get("booking_url"),
            branches=overrides.get("branches"),
            reusable_images=overrides.get("reusable_images"),
            whatsapp_url=whatsapp_url,
            social_links=social_links,
        )

        return DentalDemoPresentation(
            status=demo.status,
            template_id=demo.template_id,
            business=business_data,
            customization=customization,
        )

    @staticmethod
    async def track_event(
        session: AsyncSession,
        token: str,
        event_data: DemoEventCreate,
        user_agent: str | None = None,
    ) -> tuple[dict[str, Any], tuple[int, str, str] | None]:
        """Records telemetry events and returns notification metadata if an alert should be triggered."""
        if is_bot(user_agent):
            return {"status": "ignored_bot"}, None

        stmt = (
            select(ProspectDemo)
            .where(and_(ProspectDemo.token == token, ProspectDemo.status == "active"))
            .options(selectinload(ProspectDemo.business))
        )
        result = await session.execute(stmt)
        demo = result.scalars().first()

        if not demo or not demo.business:
            raise EntityNotFoundError("Demo", token)

        business: Business = demo.business
        now = datetime.now(UTC)
        should_notify = False

        if event_data.event_type == "demo_viewed":
            time_threshold = now - timedelta(minutes=15)
            recent_event_stmt = select(DemoEvent).where(
                and_(
                    DemoEvent.demo_id == demo.id,
                    DemoEvent.event_type == "demo_viewed",
                    DemoEvent.created_at >= time_threshold,
                )
            )
            if event_data.session_id:
                recent_event_stmt = recent_event_stmt.where(
                    DemoEvent.session_id == event_data.session_id
                )

            recent_res = await session.execute(recent_event_stmt)
            if not recent_res.scalars().first():
                demo.view_count += 1
                demo.last_viewed_at = now
                should_notify = True
        elif event_data.event_type in ("whatsapp_clicked", "call_clicked", "cta_clicked"):
            should_notify = True

        demo_event = DemoEvent(
            demo_id=demo.id,
            event_type=event_data.event_type,
            session_id=event_data.session_id,
            page_path=event_data.page_path,
            referrer=event_data.referrer,
            user_agent=user_agent[:500] if user_agent else None,
            metadata_json=event_data.metadata_json,
            created_at=now,
        )
        session.add(demo_event)
        await session.commit()

        notification_info = (
            (business.id, business.business_name, event_data.event_type) if should_notify else None
        )
        return {"status": "recorded", "event_type": event_data.event_type}, notification_info
