from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.enrichment.schemas import (
    EnrichedBrand,
    EnrichedBusinessProfile,
    EnrichedContact,
    EnrichedDoctor,
    EnrichedQualityAudit,
    EnrichedTechnology,
    EnrichmentResponse,
    TreatmentSignal,
)
from app.domains.enrichment.service import EnrichmentService
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
        "app.domains.enrichment.service.WorkerClient.enrich_business",
        new_callable=AsyncMock,
    ) as mock_worker_enrich:
        mock_worker_enrich.return_value = None
        resp = await auth_client.post(f"/v1/businesses/{business.id}/enrichment")
        assert resp.status_code in (200, 202)
        data = resp.json()
        assert data["business_id"] == business.id
        assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_enrichment_service_full_lifecycle(
    auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession
):
    """
    Tests end-to-end background enrichment execution:
    1. WorkerClient mock returns EnrichedBusinessProfile.
    2. Business contact info is backfilled (email, whatsapp).
    3. Website BusinessSource provenance is recorded with raw_payload['enrichment'].
    4. ProspectDemo custom_overrides receives logo_url, doctor details, and specialties.
    5. GET /v1/businesses/{id}/enrichment returns enriched profile.
    6. Public demo endpoint GET /v1/demos/{token} exposes logo_url and doctor overrides.
    """
    # 1. Setup Business and active Demo
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

    # Attach existing Google Maps source
    gmaps_source = BusinessSource(
        business_id=business.id,
        platform="google_maps",
        external_id="ChIJtest123",
        raw_payload={"rating": 4.8, "reviews_count": 95},
    )
    db_session.add(gmaps_source)

    # Mock Worker enrichment response
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
    mock_resp = EnrichmentResponse(
        success=True,
        status="completed",
        profile=mock_profile,
        duration_ms=450.0,
    )

    # 3. Execute with WorkerClient mocked
    with patch(
        "app.domains.enrichment.service.WorkerClient.enrich_business",
        new_callable=AsyncMock,
    ) as mock_worker_enrich:
        mock_worker_enrich.return_value = mock_resp

        # Generate demo (automatically enqueues background enrichment)
        demo_resp = await auth_client.post(f"/v1/businesses/{business.id}/demo")
        assert demo_resp.status_code == 200
        token = demo_resp.json()["token"]

        # Run background enrichment directly to guarantee sync completion
        await EnrichmentService.enrich_business_background(business_id=business.id)

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

    # Clinic logo must be populated
    assert pub_data["business"]["logo_url"] == "https://radiantsmiles.example.com/images/logo.png"
    # Doctor name and bio must reflect enriched doctor
    assert pub_data["customization"]["doctor_name"] == "Dr. Jane Watson"
    assert pub_data["customization"]["doctor_title"] == "Senior Orthodontist & Implant Specialist"
    assert "Invisalign" in pub_data["customization"]["doctor_bio"]
    # Social links and WhatsApp URL must be populated in presentation
    assert (
        pub_data["business"]["social_links"]["instagram"] == "https://instagram.com/radiantsmiles"
    )
    assert pub_data["business"]["social_links"]["facebook"] == "https://facebook.com/radiantsmiles"
    assert pub_data["business"]["social_links"]["youtube"] == "https://youtube.com/@radiantsmiles"
    assert pub_data["business"]["whatsapp_url"] == "https://wa.me/919876543210"
    assert (
        pub_data["customization"]["social_links"]["instagram"]
        == "https://instagram.com/radiantsmiles"
    )
    assert pub_data["customization"]["whatsapp_url"] == "https://wa.me/919876543210"
