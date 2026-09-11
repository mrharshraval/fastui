from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.enrichment.schemas import (
    EnrichedBranch,
    EnrichedBrand,
    EnrichedBusinessProfile,
    EnrichedContact,
    EnrichedDoctor,
    EnrichedFAQ,
    EnrichedQualityAudit,
    EnrichedTechnology,
    EnrichedTestimonial,
    EnrichmentResponse,
    TreatmentSignal,
)
from app.domains.enrichment.service import EnrichmentService
from app.domains.models import Business, CrawledWebsite


def create_mock_profile(domain: str, phone: str, address: str, doctor_name: str = "Dr. Jane Smith"):
    return EnrichedBusinessProfile(
        website_url=f"https://{domain}",
        canonical_url=f"https://{domain}",
        brand=EnrichedBrand(
            logo_url=f"https://{domain}/logo.png",
            tagline="Gentle Smiles, Modern Care",
            about_text="We have been serving our local community for over 15 years with gentle, comprehensive dental treatments.",
            brand_colors={"primary": "#0D9488", "secondary": "#1E293B"},
        ),
        primary_doctor=EnrichedDoctor(
            name=doctor_name,
            title="Senior Dental Surgeon",
            bio="Specialist in painless restorative dentistry and cosmetic rehabilitation.",
            photo_url=f"https://{domain}/doctor.jpg",
            degrees=["BDS", "MDS"],
            is_primary=True,
        ),
        doctors=[
            EnrichedDoctor(
                name=doctor_name,
                title="Senior Dental Surgeon",
                bio="Specialist in painless restorative dentistry.",
                photo_url=f"https://{domain}/doctor.jpg",
                degrees=["BDS", "MDS"],
                is_primary=True,
            )
        ],
        treatments={
            "Cosmetic Dentistry": TreatmentSignal(
                category="Cosmetic Dentistry",
                confidence=0.95,
                detected_terms=["whitening", "veneers"],
            )
        },
        contact=EnrichedContact(
            emails=[f"contact@{domain}"],
            phone_numbers=[phone],
            address=address,
            booking_url=f"https://{domain}/book",
        ),
        technology=EnrichedTechnology(cms="Next.js"),
        quality=EnrichedQualityAudit(score=95, has_ssl=True, has_mobile_viewport=True),
        testimonials=[
            EnrichedTestimonial(
                name="Aarav Sharma",
                quote="The most gentle root canal experience I have ever had. The clinic is spotless.",
                rating=5.0,
            )
        ],
        faqs=[
            EnrichedFAQ(
                question="Do you offer emergency appointments?",
                answer="Yes, same-day emergency slots are reserved daily.",
            )
        ],
        facilities=["CBCT 3D Imaging", "Digital X-Rays", "Sterilization Protocol"],
        certifications=["ISO Certified", "IDA Member"],
        insurance_info={"providers": ["Star Health", "HDFC ERGO", "Cigna"], "has_emi": True},
        emergency_services="24/7 Immediate Emergency Relief",
        unique_selling_points=["15+ Years Clinical Excellence", "10,000+ Happy Patients"],
        branches=[
            EnrichedBranch(
                name="Main Branch",
                address=address,
                phone=phone,
            )
        ],
    )


@pytest.mark.asyncio
async def test_corroborated_cache_hit_same_domain_and_phone(db_session: AsyncSession):
    """
    Verifies that when a second prospect shares the normalized domain AND has
    corroborating phone/location evidence, the cached intelligence is reused (0s crawl time).
    """
    domain = "smilespecialists.com"
    phone = "+919830012345"

    # 1. First prospect triggers fresh crawl
    prospect_1 = Business(
        business_name="Smile Specialists Kolkata",
        category="Dental Clinic",
        website=f"https://{domain}/kolkata",
        phone=phone,
        address="12A Rashbehari Avenue",
        city="Kolkata",
        postal_code="700026",
    )
    db_session.add(prospect_1)
    await db_session.commit()
    await db_session.refresh(prospect_1)

    mock_profile = create_mock_profile(
        domain=domain, phone=phone, address="12A Rashbehari Avenue, Kolkata 700026"
    )
    mock_resp = EnrichmentResponse(success=True, status="completed", profile=mock_profile)

    with patch(
        "app.domains.enrichment.service.WorkerClient.enrich_business", new_callable=AsyncMock
    ) as mock_worker:
        mock_worker.return_value = mock_resp
        profile_1, is_reused_1 = await EnrichmentService.get_or_enrich_website(
            prospect_1, db_session
        )
        assert is_reused_1 is False
        assert profile_1 is not None
        assert profile_1.brand.tagline == "Gentle Smiles, Modern Care"
        assert mock_worker.call_count == 1

    # 2. Verify CrawledWebsite record was persisted
    stmt = select(CrawledWebsite).where(CrawledWebsite.domain == domain)
    res = await db_session.execute(stmt)
    crawled_records = res.scalars().all()
    assert len(crawled_records) == 1
    assert crawled_records[0].domain == domain

    # 3. Second prospect with same domain and matching phone/location
    prospect_2 = Business(
        business_name="Smile Specialists Rashbehari",
        category="Dental Clinic",
        website=f"http://www.{domain}",
        phone=phone,
        address="12A Rashbehari Ave, Kalighat",
        city="Kolkata",
        postal_code="700026",
    )
    db_session.add(prospect_2)
    await db_session.commit()
    await db_session.refresh(prospect_2)

    # WorkerClient MUST NOT be called because corroborated cache hit occurs
    with patch(
        "app.domains.enrichment.service.WorkerClient.enrich_business", new_callable=AsyncMock
    ) as mock_worker_2:
        mock_worker_2.side_effect = AssertionError(
            "WorkerClient should not be called on cache hit!"
        )
        profile_2, is_reused_2 = await EnrichmentService.get_or_enrich_website(
            prospect_2, db_session
        )
        assert is_reused_2 is True
        assert profile_2 is not None
        assert profile_2.brand.tagline == "Gentle Smiles, Modern Care"
        assert profile_2.primary_doctor.name == "Dr. Jane Smith"
        assert mock_worker_2.call_count == 0


@pytest.mark.asyncio
async def test_branch_divergence_rejects_blind_reuse(db_session: AsyncSession):
    """
    Verifies that when two prospects share the same domain but represent DIFFERENT branches
    (conflicting postal codes and phone numbers), candidate cached intelligence is REJECTED
    and blind reuse is prevented.
    """
    domain = "nationaldentalchain.in"

    # 1. Kolkata Branch
    kolkata_prospect = Business(
        business_name="National Dental Salt Lake",
        category="Dental Clinic",
        website=f"https://{domain}/salt-lake",
        phone="+919830055555",
        address="Sector 1, Salt Lake City",
        city="Kolkata",
        postal_code="700064",
    )
    db_session.add(kolkata_prospect)
    await db_session.commit()
    await db_session.refresh(kolkata_prospect)

    kolkata_profile = create_mock_profile(
        domain=domain,
        phone="+919830055555",
        address="Sector 1, Salt Lake City, Kolkata 700064",
        doctor_name="Dr. Amit Roy",
    )
    kolkata_resp = EnrichmentResponse(success=True, status="completed", profile=kolkata_profile)

    with patch(
        "app.domains.enrichment.service.WorkerClient.enrich_business", new_callable=AsyncMock
    ) as mock_worker:
        mock_worker.return_value = kolkata_resp
        p1, reused_1 = await EnrichmentService.get_or_enrich_website(kolkata_prospect, db_session)
        assert reused_1 is False
        assert p1.primary_doctor.name == "Dr. Amit Roy"

    # 2. Mumbai Branch: same domain, but completely different city, postal code, and phone!
    mumbai_prospect = Business(
        business_name="National Dental Bandra",
        category="Dental Clinic",
        website=f"https://{domain}/mumbai-bandra",
        phone="+919820077777",
        address="Hill Road, Bandra West",
        city="Mumbai",
        postal_code="400050",
    )
    db_session.add(mumbai_prospect)
    await db_session.commit()
    await db_session.refresh(mumbai_prospect)

    mumbai_profile = create_mock_profile(
        domain=domain,
        phone="+919820077777",
        address="Hill Road, Bandra West, Mumbai 400050",
        doctor_name="Dr. Rohan Mehta",
    )
    mumbai_resp = EnrichmentResponse(success=True, status="completed", profile=mumbai_profile)

    # WorkerClient MUST be called because the Kolkata cached record was rejected for Mumbai
    with patch(
        "app.domains.enrichment.service.WorkerClient.enrich_business", new_callable=AsyncMock
    ) as mock_worker_mumbai:
        mock_worker_mumbai.return_value = mumbai_resp
        p2, reused_2 = await EnrichmentService.get_or_enrich_website(mumbai_prospect, db_session)
        assert reused_2 is False
        assert mock_worker_mumbai.call_count == 1
        assert p2.primary_doctor.name == "Dr. Rohan Mehta"

    # Confirm two distinct CrawledWebsite entries exist for the domain with different location signatures
    stmt = select(CrawledWebsite).where(CrawledWebsite.domain == domain)
    res = await db_session.execute(stmt)
    records = res.scalars().all()
    assert len(records) == 2
    signatures = {r.location_signature for r in records}
    assert len(signatures) == 2


@pytest.mark.asyncio
async def test_create_demo_route_personalization_flow(
    auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession
):
    """
    Verifies the complete Create Demo flow:
    1. Prospect has website.
    2. POST /businesses/{id}/demo executes corroborated website enrichment.
    3. Demo custom_overrides receives authentic tagline, doctor, testimonials, facilities, emergency info.
    4. GET /v1/demos/{token} exposes personalized payload to client demo.
    """
    domain = "artisandental.com"
    phone = "+919876543210"

    business = Business(
        business_name="Artisan Dental Spa",
        category="Dental Clinic",
        website=f"https://{domain}",
        phone=phone,
        address="100 Boulevard Road",
        city="Bangalore",
        state="Karnataka",
        postal_code="560001",
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    mock_profile = create_mock_profile(
        domain=domain, phone=phone, address="100 Boulevard Road, Bangalore 560001"
    )
    mock_resp = EnrichmentResponse(success=True, status="completed", profile=mock_profile)

    with patch(
        "app.domains.enrichment.service.WorkerClient.enrich_business", new_callable=AsyncMock
    ) as mock_worker:
        mock_worker.return_value = mock_resp

        # Create Demo API call
        demo_resp = await auth_client.post(f"/v1/businesses/{business.id}/demo")
        assert demo_resp.status_code == 200
        data = demo_resp.json()
        token = data["token"]
        overrides = data["custom_overrides"]

        # Assert personalized overrides were generated
        assert overrides["tagline"] == "Gentle Smiles, Modern Care"
        assert overrides["doctor_name"] == "Dr. Jane Smith"
        assert len(overrides["testimonials"]) == 1
        assert overrides["testimonials"][0]["name"] == "Aarav Sharma"
        assert "CBCT 3D Imaging" in overrides["facilities"]
        assert overrides["emergency_info"] == "24/7 Immediate Emergency Relief"
        assert overrides["booking_url"] == f"https://{domain}/book"

    # Public Demo Presentation API
    pub_resp = await client.get(f"/v1/demos/{token}")
    assert pub_resp.status_code == 200
    pub = pub_resp.json()

    assert pub["customization"]["tagline"] == "Gentle Smiles, Modern Care"
    assert pub["customization"]["doctor_name"] == "Dr. Jane Smith"
    assert pub["customization"]["emergency_info"] == "24/7 Immediate Emergency Relief"
    assert pub["customization"]["booking_url"] == f"https://{domain}/book"
    assert len(pub["customization"]["testimonials"]) == 1
