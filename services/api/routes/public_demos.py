import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from models.database import get_db
from models.schema import ProspectDemo, DemoEvent, Business, BusinessSource, utc_now
from schemas.demos import (
    DentalDemoPresentation,
    DentalBusinessPresentation,
    DentalCustomization,
    DemoEventCreate,
)
from services.push_service import PushNotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/v1/demos", tags=["Public Demos"])

BOT_REGEX = re.compile(
    r"(bot|crawl|spider|slurp|facebookexternalhit|whatsapp|telegram|twitterbot|slackbot|discordbot|lighthouse|embedly|preview|headlesschrome)",
    re.IGNORECASE
)


def _is_bot(user_agent: Optional[str]) -> bool:
    if not user_agent:
        return False
    return bool(BOT_REGEX.search(user_agent))


@router.get("/{token}", response_model=DentalDemoPresentation)
async def get_public_demo_by_token(
    token: str,
    response: Response,
    session: AsyncSession = Depends(get_db)
):
    """
    Public presentation endpoint for prospect dental demos.
    Resolves the unguessable 24-character token to dynamic business presentation data.
    Sanitized: Excludes internal CRM fields, tokens, and leads.
    Cached: Private client cache bound to the full token.
    """
    stmt = (
        select(ProspectDemo)
        .where(and_(ProspectDemo.token == token, ProspectDemo.status == "active"))
        .options(
            selectinload(ProspectDemo.business).selectinload(Business.sources)
        )
    )
    result = await session.execute(stmt)
    demo = result.scalars().first()

    if not demo or not demo.business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found or has expired."
        )

    business: Business = demo.business

    # Extract scraped metadata from Google Maps source if present
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

    # Resolve customization with prospect overrides if specified
    overrides = demo.custom_overrides or {}

    # Resolve clinic logo from overrides or enrichment payload
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

    # Build sanitized business presentation payload
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
        branches=overrides.get("branches")
    )
    customization = DentalCustomization(
        hero_headline=overrides.get("hero_headline", "Where healthy smiles begin."),
        hero_subheadline=overrides.get(
            "hero_subheadline",
            f"Comprehensive, gentle dental care tailored to your family's needs in {business.city or 'our community'}."
        ),
        hero_image_url=overrides.get("hero_image_url", "/hero_dentist_v1.webp"),
        doctor_name=overrides.get("doctor_name", "Dr. Sarah Jenkins"),
        doctor_title=overrides.get("doctor_title", "Chief Dental Surgeon"),
        doctor_bio=overrides.get(
            "doctor_bio",
            "Specializing in cosmetic dentistry, dental implants, and compassionate preventive dental care."
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

    # Set private cache header bound to token
    response.headers["Cache-Control"] = "private, max-age=300"

    return DentalDemoPresentation(
        status=demo.status,
        template_id=demo.template_id,
        business=business_data,
        customization=customization
    )


@router.post("/{token}/events")
async def track_demo_event(
    token: str,
    event_data: DemoEventCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    """
    Record engagement events from the public demo site.
    Filters bots, deduplicates repeated view events within 15 minutes,
    and broadcasts instant push notifications to all sales devices on meaningful views.
    """
    user_agent = request.headers.get("user-agent", "")
    is_bot = _is_bot(user_agent)

    stmt = (
        select(ProspectDemo)
        .where(and_(ProspectDemo.token == token, ProspectDemo.status == "active"))
        .options(selectinload(ProspectDemo.business))
    )
    result = await session.execute(stmt)
    demo = result.scalars().first()

    if not demo or not demo.business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found or has expired."
        )

    business: Business = demo.business

    # If it's a known crawler, do not trigger alerts or pollute metrics
    if is_bot:
        return {"status": "ignored_bot"}

    now = utc_now()
    should_notify = False

    if event_data.event_type == "demo_viewed":
        # Deduplicate views within 15 minutes by session_id or demo_id
        time_threshold = now - timedelta(minutes=15)
        recent_event_stmt = select(DemoEvent).where(
            and_(
                DemoEvent.demo_id == demo.id,
                DemoEvent.event_type == "demo_viewed",
                DemoEvent.created_at >= time_threshold
            )
        )
        if event_data.session_id:
            recent_event_stmt = recent_event_stmt.where(DemoEvent.session_id == event_data.session_id)

        recent_res = await session.execute(recent_event_stmt)
        recent_view = recent_res.scalars().first()

        if not recent_view:
            demo.view_count += 1
            demo.last_viewed_at = now
            should_notify = True
    elif event_data.event_type in ("whatsapp_clicked", "call_clicked", "cta_clicked"):
        should_notify = True

    # Record event in demo_events table
    demo_event = DemoEvent(
        demo_id=demo.id,
        event_type=event_data.event_type,
        session_id=event_data.session_id,
        page_path=event_data.page_path,
        referrer=event_data.referrer,
        user_agent=user_agent[:500] if user_agent else None,
        metadata_json=event_data.metadata_json
    )
    session.add(demo_event)
    await session.commit()

    # Trigger team-wide push notification if significant event
    if should_notify:
        if event_data.event_type == "demo_viewed":
            push_title = "🔥 Prospect Viewed Demo!"
            push_body = f"{business.business_name} just opened their personalized website demo."
        elif event_data.event_type == "whatsapp_clicked":
            push_title = "💬 WhatsApp Clicked on Demo!"
            push_body = f"Prospect from {business.business_name} clicked the WhatsApp chat button!"
        elif event_data.event_type == "call_clicked":
            push_title = "📞 Call Clicked on Demo!"
            push_body = f"Prospect from {business.business_name} clicked to call the clinic!"
        else:
            push_title = "⚡ Prospect Engaged with Demo!"
            push_body = f"{business.business_name} took action: {event_data.event_type.replace('_', ' ').title()}"

        push_payload = {
            "title": push_title,
            "body": push_body,
            "data": {
                "business_id": business.id,
                "url": f"/business/{business.id}",
                "event_type": event_data.event_type
            }
        }

        # Dispatch async broadcast to all sales devices
        background_tasks.add_task(
            PushNotificationService.broadcast_to_all_accounts,
            session,
            push_payload
        )

    return {"status": "recorded", "event_type": event_data.event_type}
