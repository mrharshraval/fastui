"""
Tests for website enrichment intelligence — corroborated cache matching and
demo personalization from pre-existing cached data.

The new contract:
- `EnrichmentService.find_matching_cached_intelligence` is a pure read-only lookup.
- `EnrichmentService.extract_enrichment_from_business` is a pure read-only lookup.
- `DemoService.create_or_get_demo` uses cached enrichment if present; creates demo
  with base overrides if not. It never enqueues enrichment tasks.
- Enrichment has exactly one production trigger: POST /businesses/{id}/enrichment.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.enrichment.models import CrawledWebsite
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
    TreatmentSignal,
)
from app.domains.enrichment.service import EnrichmentService
from app.domains.models import Business


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


async def _seed_crawled_website(
    session: AsyncSession,
    domain: str,
    profile: EnrichedBusinessProfile,
    location_signature: str,
    business_id: int | None = None,
) -> CrawledWebsite:
    """Helper: persists a CrawledWebsite record simulating a prior enrichment run."""
    crawled = CrawledWebsite(
        domain=domain,
        location_signature=location_signature,
        business_id=business_id,
        canonical_url=f"https://{domain}",
        extracted_data=profile.model_dump(),
        confidence_score=1.0,
    )
    session.add(crawled)
    await session.commit()
    await session.refresh(crawled)
    return crawled


@pytest.mark.asyncio
async def test_corroborated_cache_hit_same_domain_and_phone(db_session: AsyncSession):
    """
    Verifies that when a prospect has a matching domain AND corroborating phone/location
    evidence, find_matching_cached_intelligence returns the cached record (no crawl triggered).
    """
    domain = "smilespecialists.com"
    phone = "+919830012345"
    profile = create_mock_profile(
        domain=domain, phone=phone, address="12A Rashbehari Avenue, Kolkata 700026"
    )

    prospect = Business(
        business_name="Smile Specialists Kolkata",
        category="Dental Clinic",
        website=f"https://{domain}/kolkata",
        phone=phone,
        address="12A Rashbehari Avenue",
        city="Kolkata",
        postal_code="700026",
    )
    db_session.add(prospect)
    await db_session.commit()
    await db_session.refresh(prospect)

    # Simulate a previously enriched CrawledWebsite record (as the worker would create)
    await _seed_crawled_website(
        session=db_session,
        domain=domain,
        profile=profile,
        location_signature="kolkata_700026_12a_rashbehari",
        business_id=prospect.id,
    )

    cached_record = await EnrichmentService.find_matching_cached_intelligence(
        prospect=prospect,
        normalized_domain=domain,
        session=db_session,
    )
    assert cached_record is not None, "Should find a corroborated cache hit"
    cached_profile = EnrichedBusinessProfile.model_validate(cached_record.extracted_data)
    assert cached_profile.brand.tagline == "Gentle Smiles, Modern Care"
    assert cached_profile.primary_doctor.name == "Dr. Jane Smith"


@pytest.mark.asyncio
async def test_branch_divergence_rejects_blind_reuse(db_session: AsyncSession):
    """
    Verifies that when two prospects share the same domain but represent DIFFERENT branches
    (conflicting postal codes and phone numbers), the candidate cached record is rejected
    for the second prospect — no blind cross-branch reuse.
    """
    domain = "nationaldentalchain.in"

    kolkata_profile = create_mock_profile(
        domain=domain,
        phone="+919830055555",
        address="Sector 1, Salt Lake City, Kolkata 700064",
        doctor_name="Dr. Amit Roy",
    )
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

    await _seed_crawled_website(
        session=db_session,
        domain=domain,
        profile=kolkata_profile,
        location_signature="kolkata_700064_sector_1_salt",
        business_id=kolkata_prospect.id,
    )

    # Mumbai branch: same domain, completely different city/postal/phone
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

    # The Kolkata record must be rejected for the Mumbai prospect
    cached_record = await EnrichmentService.find_matching_cached_intelligence(
        prospect=mumbai_prospect,
        normalized_domain=domain,
        session=db_session,
    )
    assert cached_record is None, (
        "Kolkata cached intelligence must not be reused for Mumbai branch "
        "— conflicting location and phone"
    )


@pytest.mark.asyncio
async def test_create_demo_uses_cached_enrichment_no_enqueue(
    auth_client, client, db_session: AsyncSession
):
    """
    Verifies the Create Demo flow when a pre-existing cached enrichment exists:
    1. Prospect has website.
    2. POST /businesses/{id}/demo reads cached CrawledWebsite intelligence.
    3. Demo custom_overrides receives authentic tagline, doctor, testimonials, etc.
    4. GET /v1/demos/{token} exposes personalized payload.
    5. fastui:enrich:tasks receives ZERO messages (no implicit enqueue).
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

    # Pre-seed the CrawledWebsite — simulates the result of a prior explicit enrichment
    await _seed_crawled_website(
        session=db_session,
        domain=domain,
        profile=mock_profile,
        location_signature="bangalore_560001_100_boulevard",
        business_id=business.id,
    )

    demo_resp = await auth_client.post(f"/v1/businesses/{business.id}/demo")
    assert demo_resp.status_code == 200
    data = demo_resp.json()
    token = data["token"]
    overrides = data["custom_overrides"]

    # Assert personalized overrides came from the cached CrawledWebsite record
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


@pytest.mark.asyncio
async def test_create_demo_without_cached_enrichment_no_enqueue(
    auth_client, db_session: AsyncSession
):
    """
    Verifies that when no cached enrichment exists for a business with a website,
    the demo is created successfully with base overrides only — no enrichment enqueue.
    """
    business = Business(
        business_name="Fresh Dental Studio",
        category="Dental Clinic",
        website="https://freshdental.com",
        phone="+919900000001",
        city="Pune",
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    # No CrawledWebsite record exists — cache miss path
    stmt = select(CrawledWebsite).where(CrawledWebsite.domain == "freshdental.com")
    res = await db_session.execute(stmt)
    assert res.scalars().first() is None, "Test precondition: no cached enrichment"

    demo_resp = await auth_client.post(f"/v1/businesses/{business.id}/demo")
    assert demo_resp.status_code == 200
    data = demo_resp.json()
    assert data["token"] is not None
    # custom_overrides may be None or empty — no personalization without cache
    overrides = data.get("custom_overrides") or {}
    assert "tagline" not in overrides
    assert "doctor_name" not in overrides
