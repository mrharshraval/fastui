"""FastUI Business Domain Response Mapping.

Decoupled mapping functions converting database models to presentation DTOs without circular dependencies.
"""

from app.domains.businesses.models import Business, BusinessSource
from app.domains.businesses.schemas import BusinessResponse
from app.domains.leads.models import Lead


def map_business_response(
    business: Business,
    lead: Lead | None = None,
    maps_src: BusinessSource | None = None,
) -> BusinessResponse:
    """Canonical mapping from Business, Lead, and Source models to BusinessResponse DTO."""
    lead_stage = (
        lead.stage.value
        if lead and hasattr(lead.stage, "value")
        else (str(lead.stage) if lead else None)
    )
    lead_priority = lead.priority.value if lead and hasattr(lead.priority, "value") else "medium"
    lead_signal = lead.signal.value if lead and hasattr(lead.signal, "value") else "warm"
    lead_score = lead.score if lead else 50
    lead_id = lead.id if lead else None
    is_lead = lead is not None

    maps_url = maps_src.source_url if maps_src else None
    maps_place_id = maps_src.external_id if maps_src else None
    lat = None
    lng = None
    if maps_src and isinstance(maps_src.raw_payload, dict):
        lat = maps_src.raw_payload.get("latitude")
        lng = maps_src.raw_payload.get("longitude")
        if not maps_place_id:
            maps_place_id = maps_src.raw_payload.get("place_id")

    return BusinessResponse(
        id=business.id,
        business_name=business.business_name,
        category=business.category,
        phone=business.phone,
        email=business.email,
        website=business.website,
        has_whatsapp=business.has_whatsapp,
        address=business.address,
        city=business.city,
        state=business.state,
        country=business.country,
        postal_code=business.postal_code,
        website_status=(
            business.website_status.value
            if hasattr(business.website_status, "value")
            else str(business.website_status)
        ),
        qualification_status=business.qualification_status or "unqualified",
        is_lead=is_lead,
        pipeline_stage=lead_stage,
        stage=lead_stage,
        priority=lead_priority,
        signal=lead_signal,
        score=lead_score,
        lead_id=lead_id,
        google_maps_url=maps_url,
        latitude=lat,
        longitude=lng,
        google_place_id=maps_place_id,
        last_outreach_at=business.last_outreach_at.isoformat()
        if business.last_outreach_at
        else None,
        last_contacted_at=business.last_contacted_at.isoformat()
        if business.last_contacted_at
        else None,
        created_at=business.created_at.isoformat() if business.created_at else None,
        updated_at=business.updated_at.isoformat() if business.updated_at else None,
    )
