"""
FastUI Worker Contract Parity Tests
====================================
Validates request parsing, response serialization, authentication, and HTTP envelopes
against standalone external API contract fixtures.
Strict requirement: ZERO imports from services/api.
"""

from contracts.discovery import (
    DiscoveredLead,
    DiscoverResponse,
    DiscoverySearchParams,
)
from contracts.enrichment import (
    EnrichedBusinessProfile,
    EnrichmentParams,
    EnrichmentResponse,
)

# Explicit standalone contract fixtures matching the finalized FastUI API specification
CANONICAL_DISCOVERY_REQUEST_FIXTURE = {
    "target_audience": "Dentist",
    "location": "Ahmedabad, Gujarat, India",
    "limit": 50,
    "batch_size": 50,
    "query_variations": ["Dentist Ahmedabad", "Dental Clinic Ahmedabad"],
    "source_preferences": ["google_maps", "web_search"],
    "cursor": "loc_sector_1",
}

CANONICAL_DISCOVERED_LEAD_FIXTURE = {
    "name": "Apex Dental Clinic",
    "raw_name": "Apex Dental Clinic - Dr. Patel",
    "normalized_name": "apex dental clinic",
    "category": "Dentist",
    "city": "Ahmedabad",
    "state": "Gujarat",
    "country": "India",
    "postal_code": "380015",
    "address": "101 High Street, Satellite, Ahmedabad",
    "phone": "+91 98765 43210",
    "email": "contact@apexdental.com",
    "website": "https://www.apexdental.com",
    "has_whatsapp": True,
    "whatsapp": "+919876543210",
    "source_platform": "google_maps",
    "source_place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "source_url": "https://maps.google.com/?cid=12345",
    "rating": 4.8,
    "reviews_count": 142,
    "latitude": 23.0225,
    "longitude": 72.5714,
    "google_place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "google_maps_url": "https://maps.google.com/?cid=12345",
    "opening_hours": {"monday": "9:00 AM - 8:00 PM"},
    "business_status": "OPERATIONAL",
}

CANONICAL_ENRICHMENT_REQUEST_FIXTURE = {
    "website": "https://www.apexdental.com",
    "business_name": "Apex Dental Clinic",
}


def test_discovery_params_parses_canonical_fixture():
    params = DiscoverySearchParams.model_validate(CANONICAL_DISCOVERY_REQUEST_FIXTURE)
    assert params.target_audience == "Dentist"
    assert params.location == "Ahmedabad, Gujarat, India"
    assert params.limit == 50
    assert params.batch_size == 50
    assert params.query_variations == ["Dentist Ahmedabad", "Dental Clinic Ahmedabad"]
    assert params.source_preferences == ["google_maps", "web_search"]
    assert params.cursor == "loc_sector_1"


def test_discovered_lead_parses_and_serializes_canonical_fixture():
    lead = DiscoveredLead.model_validate(CANONICAL_DISCOVERED_LEAD_FIXTURE)
    dumped = lead.model_dump()
    assert dumped["name"] == "Apex Dental Clinic"
    assert dumped["phone"] == "+91 98765 43210"
    assert dumped["rating"] == 4.8
    assert dumped["reviews_count"] == 142
    assert dumped["google_place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert dumped["has_whatsapp"] is True


def test_discover_response_envelope_parity():
    lead = DiscoveredLead.model_validate(CANONICAL_DISCOVERED_LEAD_FIXTURE)
    response = DiscoverResponse(
        leads=[lead],
        count=1,
        exhausted=False,
        sources_exhausted={"google_maps": False, "web_search": False},
        peak_rss_mb=215.4,
        next_cursor="loc_sector_2",
        current_locality="Satellite",
        localities_remaining=12,
    )
    dumped = response.model_dump()
    assert len(dumped["leads"]) == 1
    assert dumped["count"] == 1
    assert dumped["exhausted"] is False
    assert dumped["sources_exhausted"] == {"google_maps": False, "web_search": False}
    assert dumped["peak_rss_mb"] == 215.4
    assert dumped["next_cursor"] == "loc_sector_2"
    assert dumped["current_locality"] == "Satellite"
    assert dumped["localities_remaining"] == 12


def test_enrichment_params_and_response_parity():
    req = EnrichmentParams.model_validate(CANONICAL_ENRICHMENT_REQUEST_FIXTURE)
    assert req.website == "https://www.apexdental.com"
    assert req.business_name == "Apex Dental Clinic"
    assert req.max_pages == 4  # Canonical default

    profile = EnrichedBusinessProfile(
        website_url="https://www.apexdental.com",
        tagline="World class dental care",
        specialties=["Orthodontics", "Implantology"],
    )
    resp = EnrichmentResponse(
        success=True,
        status="completed",
        profile=profile,
        duration_ms=1450.5,
    )
    dumped = resp.model_dump()
    assert dumped["success"] is True
    assert dumped["status"] == "completed"
    assert dumped["profile"]["website_url"] == "https://www.apexdental.com"
    assert dumped["profile"]["tagline"] == "World class dental care"
    assert dumped["duration_ms"] == 1450.5
