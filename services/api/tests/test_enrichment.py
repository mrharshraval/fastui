from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.enrichment.models import CrawledWebsite
from app.domains.enrichment.schemas import (
    EnrichedBrand,
    EnrichedBusinessProfile,
    EnrichedContact,
    EnrichedDoctor,
    EnrichedQualityAudit,
    EnrichedTechnology,
    TreatmentSignal,
)
from app.domains.models import Business, BusinessSource


@pytest.mark.asyncio
async def test_enrich_endpoint_no_website_returns_400(
    auth_client: AsyncClient, db_session: AsyncSession
):
    """Confirms POST /v1/businesses/{id}/enrichment fails if business has no website."""
    business = Business(
        business_name="No Website Clinic",
        category="Dental Clinic",
        city="Ahmedabad",
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    resp = await auth_client.post(f"/v1/businesses/{business.id}/enrichment")
    assert resp.status_code == 400
    assert "does not have a website" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_enrich_endpoint_queues_background_task(
    auth_client: AsyncClient, db_session: AsyncSession
):
    """Confirms POST /v1/businesses/{id}/enrichment queues background task and returns 202."""
    business = Business(
        business_name="Apex Dental Care",
        category="Dental Clinic",
        website="https://apexdental.example.com",
        city="Ahmedabad",
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    with patch(
        "app.domains.enrichment.service._redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_xadd:
        resp = await auth_client.post(f"/v1/businesses/{business.id}/enrichment")
        assert resp.status_code in (200, 202)
        data = resp.json()
        assert data["business_id"] == business.id
        assert data["status"] == "queued"

        mock_xadd.assert_called_once_with(
            "fastui:enrich:tasks",
            {
                "business_id": str(business.id),
                "website": "https://apexdental.example.com",
                "business_name": "Apex Dental Care",
            },
        )


@pytest.mark.asyncio
async def test_enrichment_service_full_lifecycle(
    auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession
):
    """
    Tests end-to-end explicit enrichment flow:
    1. Explicit POST /v1/businesses/{id}/enrichment queues task to fastui:enrich:tasks.
    2. Simulated worker saves enriched profile into CrawledWebsite and BusinessSource.
    3. GET /v1/businesses/{id}/enrichment returns enriched profile.
    4. Public demo endpoint GET /v1/demos/{token} exposes logo_url and doctor overrides.
    """
    business = Business(
        business_name="Radiant Smiles Dental",
        category="Dentist",
        website="https://radiantsmiles.example.com",
        city="Ahmedabad",
        state="Gujarat",
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    mock_profile = EnrichedBusinessProfile(
        website_url="https://radiantsmiles.example.com",
        canonical_url="https://radiantsmiles.example.com",
        brand=EnrichedBrand(
            logo_url="https://radiantsmiles.example.com/images/logo.png",
            favicon_url="https://radiantsmiles.example.com/favicon.ico",
            primary_color="#1E40AF",
        ),
        primary_doctor=EnrichedDoctor(
            name="Dr. Jane Watson",
            title="Senior Orthodontist & Implant Specialist",
            bio="Over 12 years of clinical expertise in Invisalign and digital smile design.",
            degrees=["BDS", "MDS Orthodontics"],
            is_primary=True,
        ),
        treatments={
            "Orthodontics": TreatmentSignal(
                category="Orthodontics",
                detected_terms=["invisalign", "braces"],
                confidence=0.9,
                source="body",
            ),
            "Dental Implants": TreatmentSignal(
                category="Dental Implants",
                detected_terms=["all-on-4", "implants"],
                confidence=0.85,
                source="body",
            ),
        },
        contact=EnrichedContact(
            emails=["info@radiantsmiles.example.com"],
            phone_numbers=["+919876543210"],
            whatsapp_url="https://wa.me/919876543210",
            social_links={
                "instagram": "https://instagram.com/radiantsmiles",
                "facebook": "https://facebook.com/radiantsmiles",
                "youtube": "https://youtube.com/@radiantsmiles",
            },
        ),
        technology=EnrichedTechnology(cms="WordPress", analytics=["Google Analytics 4"]),
        quality=EnrichedQualityAudit(score=92, has_ssl=True, has_mobile_viewport=True),
    )

    # 1. Trigger explicit enrichment
    with patch(
        "app.domains.enrichment.service._redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_xadd:
        resp = await auth_client.post(f"/v1/businesses/{business.id}/enrichment")
        assert resp.status_code in (200, 202)
        mock_xadd.assert_called_once_with(
            "fastui:enrich:tasks",
            {
                "business_id": str(business.id),
                "website": "https://radiantsmiles.example.com",
                "business_name": "Radiant Smiles Dental",
            },
        )

    # 2. Simulate worker saving enrichment output
    gmaps_source = BusinessSource(
        business_id=business.id,
        platform="google_maps",
        external_id="ChIJtest123",
        raw_payload={
            "rating": 4.8,
            "reviews_count": 95,
            "enrichment": mock_profile.model_dump(),
        },
    )
    crawled = CrawledWebsite(
        domain="radiantsmiles.example.com",
        location_signature="ahmedabad",
        business_id=business.id,
        extracted_data=mock_profile.model_dump(),
        canonical_url="https://radiantsmiles.example.com",
        confidence_score=1.0,
    )
    db_session.add(gmaps_source)
    db_session.add(crawled)
    await db_session.commit()

    # 3. Create demo (reads cached intelligence, does NOT enqueue enrichment)
    with patch(
        "app.domains.enrichment.service._redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_demo_xadd:
        demo_resp = await auth_client.post(f"/v1/businesses/{business.id}/demo")
        assert demo_resp.status_code == 200
        token = demo_resp.json()["token"]
        mock_demo_xadd.assert_not_called()

    # 4. Verify CRM Enrichment Status Endpoint
    status_resp = await auth_client.get(f"/v1/businesses/{business.id}/enrichment")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["is_enriched"] is True
    assert status_data["quality_score"] == 92
    assert status_data["brand"]["logo_url"] == "https://radiantsmiles.example.com/images/logo.png"
    assert status_data["primary_doctor"]["name"] == "Dr. Jane Watson"
    assert status_data["treatments_count"] == 2

    # 5. Verify Public Demo Presentation
    pub_resp = await client.get(f"/v1/demos/{token}")
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()

    assert pub_data["business"]["logo_url"] == "https://radiantsmiles.example.com/images/logo.png"
    assert pub_data["customization"]["doctor_name"] == "Dr. Jane Watson"
    assert pub_data["customization"]["doctor_title"] == "Senior Orthodontist & Implant Specialist"
    assert "Invisalign" in pub_data["customization"]["doctor_bio"]
    assert pub_data["business"]["social_links"]["instagram"] == "https://instagram.com/radiantsmiles"
    assert pub_data["business"]["social_links"]["facebook"] == "https://facebook.com/radiantsmiles"
    assert pub_data["business"]["social_links"]["youtube"] == "https://youtube.com/@radiantsmiles"
    assert pub_data["business"]["whatsapp_url"] == "https://wa.me/919876543210"
    assert pub_data["customization"]["social_links"]["instagram"] == "https://instagram.com/radiantsmiles"
    assert pub_data["customization"]["whatsapp_url"] == "https://wa.me/919876543210"


@pytest.mark.asyncio
async def test_discovery_pipeline_never_triggers_or_enqueues_enrichment(
    auth_client: AsyncClient, db_session: AsyncSession
):
    """
    Architectural Invariant Test:
    - Discovery job creation must enqueue only to fastui:discover:tasks, NEVER to fastui:enrich:tasks.
    - Discovered prospects (with or without websites) stored in the database must never trigger enrichment.
    - Business listing, detail querying, and demo generation must never trigger enrichment.
    - Only the explicit user POST /v1/businesses/{id}/enrichment action queues to fastui:enrich:tasks.
    """
    # 1. Create discovery job
    with patch(
        "app.domains.prospecting.service.redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_discover_xadd, patch(
        "app.domains.enrichment.service._redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_enrich_xadd:
        resp = await auth_client.post(
            "/v1/prospecting/jobs",
            json={
                "business_type": "Orthodontist",
                "location": {"city": "Chennai", "country": "India"},
                "limit": 50,
            },
        )
        assert resp.status_code in (200, 202)
        # Verify discovery task was published to fastui:discover:tasks
        mock_discover_xadd.assert_called_once()
        call_stream = mock_discover_xadd.call_args[0][0]
        assert call_stream == "fastui:discover:tasks"

        # Verify fastui:enrich:tasks was NOT touched
        mock_enrich_xadd.assert_not_called()

    # 2. Simulate discovery results persisted to DB (businesses with websites)
    b1 = Business(
        business_name="Chennai Smile Center",
        category="Orthodontist",
        website="https://chennaismiles.example.com",
        city="Chennai",
        phone="+919840011223",
        website_status="website_found",
    )
    b2 = Business(
        business_name="Marina Dental Clinic",
        category="Orthodontist",
        website="https://marinadental.example.com",
        city="Chennai",
        phone="+919840099887",
        website_status="website_found",
    )
    b3 = Business(
        business_name="Anna Nagar Dental",
        category="Orthodontist",
        website=None,
        city="Chennai",
        phone="+919840055443",
        website_status="no_website",
    )
    db_session.add_all([b1, b2, b3])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)
    await db_session.refresh(b3)

    # 3. Read operations: listing and getting businesses
    with patch(
        "app.domains.enrichment.service._redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_enrich_xadd:
        list_resp = await auth_client.get("/v1/businesses?search=Chennai")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        get_resp = await auth_client.get(f"/v1/businesses/{b1.id}")
        assert get_resp.status_code == 200

        # Create demo without prior enrichment
        demo_resp = await auth_client.post(f"/v1/businesses/{b1.id}/demo")
        assert demo_resp.status_code == 200

        # Still ZERO enrichment tasks enqueued
        mock_enrich_xadd.assert_not_called()

    # 4. Explicit user action: ONLY this enqueues to fastui:enrich:tasks
    with patch(
        "app.domains.enrichment.service._redis_client.xadd",
        new_callable=AsyncMock,
    ) as mock_enrich_xadd:
        enrich_resp = await auth_client.post(f"/v1/businesses/{b1.id}/enrichment")
        assert enrich_resp.status_code in (200, 202)
        mock_enrich_xadd.assert_called_once_with(
            "fastui:enrich:tasks",
            {
                "business_id": str(b1.id),
                "website": "https://chennaismiles.example.com",
                "business_name": "Chennai Smile Center",
            },
        )
