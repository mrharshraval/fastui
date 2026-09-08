"""
FastUI Worker Deduplication Unit Tests
======================================
Tests multi-tier identity matching and conflict rejection.
Verifies that duplicate detection is never based on business name alone.
"""

import pytest
from contracts import DiscoveredLead
from deduplication import (
    LeadDeduplicator,
    normalize_phone,
    normalize_website,
    normalize_address,
    extract_postal_code,
    are_addresses_matching,
    are_coordinates_matching,
    is_duplicate_lead,
)


def test_normalize_phone():
    assert normalize_phone("+91 98300 12345") == "+919830012345"
    assert normalize_phone("098300 12345", location="Kolkata, West Bengal, India") == "+919830012345"
    assert normalize_phone(None) is None


def test_normalize_website():
    assert normalize_website("https://www.apexdentalcare.in/contact/") == "apexdentalcare.in"
    assert normalize_website("http://sub.domain.co.in:8000") == "sub.domain.co.in"
    assert normalize_website(None) is None


def test_are_addresses_matching():
    # Same physical location with abbreviations
    assert are_addresses_matching(
        "12 Park Street, Kolkata",
        "12 Park St, Kolkata",
        city="Kolkata"
    ) is True

    # Same location with postal codes
    assert are_addresses_matching(
        "Sunrise Complex, Drive-in Rd, Ahmedabad 380054",
        "Shop 4, Sunrise Complex, Drive-in Road, Ahmedabad 380054",
        postal1="380054",
        postal2="380054",
    ) is True

    # Conflicting postal codes in same city -> False
    assert are_addresses_matching(
        "12 Park Street, Kolkata",
        "Block CJ 241, Salt Lake, Kolkata",
        postal1="700016",
        postal2="700091",
        city="Kolkata"
    ) is False

    # Conflicting street numbers -> False
    assert are_addresses_matching(
        "12 Park Street, Kolkata",
        "50 Park Street, Kolkata",
        city="Kolkata"
    ) is False

    # Different localities in same city -> False
    assert are_addresses_matching(
        "Park Street, Kolkata",
        "Salt Lake Sector V, Kolkata",
        city="Kolkata"
    ) is False


def test_are_coordinates_matching():
    # Identical
    assert are_coordinates_matching(22.5726, 88.3639, 22.5726, 88.3639) is True
    # ~50m apart
    assert are_coordinates_matching(22.5726, 88.3639, 22.5730, 88.3639) is True
    # Far apart (> 350m)
    assert are_coordinates_matching(22.5726, 88.3639, 22.6200, 88.4000) is False
    # Missing
    assert are_coordinates_matching(None, None, 22.5726, 88.3639) is None


def test_identical_name_without_supporting_metadata_is_not_duplicate():
    """
    CRITICAL REQUIREMENT: Businesses with the same name are treated as separate
    entities unless there is additional evidence that they represent the same physical business.
    """
    lead1 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
    )
    lead2 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
    )
    assert is_duplicate_lead(lead1, lead2) is False


def test_identical_name_with_different_locations_is_not_duplicate():
    """
    If the name is identical but the location indicates different businesses, do not merge.
    """
    # Different addresses
    lead1 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        address="12 Park Street, Kolkata",
        postal_code="700016",
    )
    lead2 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        address="Block CJ 241, Sector II, Salt Lake, Kolkata",
        postal_code="700091",
    )
    assert is_duplicate_lead(lead1, lead2) is False

    # Different coordinates (> 350m apart)
    lead3 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        latitude=22.5532,
        longitude=88.3512,
    )
    lead4 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        latitude=22.5855,
        longitude=88.4189,
    )
    assert is_duplicate_lead(lead3, lead4) is False

    # Different cities
    lead5 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
    )
    lead6 = DiscoveredLead(
        name="Apex Dental Care",
        city="Mumbai",
    )
    assert is_duplicate_lead(lead5, lead6) is False


def test_identical_name_with_different_phones_is_not_duplicate():
    lead1 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        phone="+919830000001",
    )
    lead2 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        phone="+919830000099",
    )
    assert is_duplicate_lead(lead1, lead2) is False


def test_identical_name_with_supporting_evidence_is_duplicate():
    # 1. Matching physical address
    lead1 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        address="12 Park Street, Kolkata",
        postal_code="700016",
    )
    lead2 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        address="12 Park St, Kolkata",
        postal_code="700016",
    )
    assert is_duplicate_lead(lead1, lead2) is True

    # 2. Matching coordinates (< 120m)
    lead3 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        latitude=22.5532,
        longitude=88.3512,
    )
    lead4 = DiscoveredLead(
        name="Apex Dental Care",
        city="Kolkata",
        latitude=22.5535,
        longitude=88.3514,
    )
    assert is_duplicate_lead(lead3, lead4) is True


def test_place_id_matching():
    # Same Google Place ID -> duplicate
    lead1 = DiscoveredLead(
        name="Apex Dental Care",
        google_place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
    )
    lead2 = DiscoveredLead(
        name="Apex Dental Care Kolkata Branch",
        google_place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
    )
    assert is_duplicate_lead(lead1, lead2) is True

    # Different Place IDs on same platform -> NOT duplicate
    lead3 = DiscoveredLead(
        name="Apex Dental Care",
        source_platform="google_maps",
        source_place_id="place_111",
    )
    lead4 = DiscoveredLead(
        name="Apex Dental Care",
        source_platform="google_maps",
        source_place_id="place_222",
    )
    assert is_duplicate_lead(lead3, lead4) is False
