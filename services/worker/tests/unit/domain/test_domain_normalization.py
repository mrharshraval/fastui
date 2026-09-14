"""
Unit tests for domain normalization functions.
Verifies pure business name, address, website, and phone normalization.
"""

from domain.normalization import (
    NormalizedBusinessName,
    normalize_address,
    normalize_business_name,
    normalize_phone,
    normalize_website,
    resolve_canonical_name,
)


def test_normalize_business_name_strips_marketing_and_punctuation():
    res = normalize_business_name("Apex Dental Care - Best Dentist in Ahmedabad [Implant Specialist] ⭐⭐⭐")
    assert isinstance(res, NormalizedBusinessName)
    assert res.display_name == "Apex Dental Care"
    assert res.normalized_name == "apex dental care"


def test_normalize_business_name_preserves_acronyms():
    res = normalize_business_name("3M Healthcare LLC")
    assert "3M" in res.display_name
    assert "LLC" in res.display_name


def test_resolve_canonical_name_reconciles_with_brand():
    source_name = "Apex Dental Clinic - Dr. Patel Satellite"
    brand_name = "Apex Dental"
    res = resolve_canonical_name(source_name, website_brand=brand_name)
    assert res.display_name == "Apex Dental"


def test_normalize_address_expands_abbreviations():
    addr = "Shop 4, 12 Park St., Drive-in Rd, Near Vastrapur Lake"
    norm = normalize_address(addr)
    assert "street" in norm
    assert "road" in norm
    assert "near" in norm


def test_normalize_website_canonical_hostname():
    assert normalize_website("https://www.apexdental.co.in/about-us?ref=123") == "apexdental.co.in"
    assert normalize_website("http://subdomain.clinic.com:8080") == "subdomain.clinic.com"
    assert normalize_website(None) is None


def test_normalize_phone_canonical_e164():
    assert normalize_phone("09876543210", location="Ahmedabad, India") == "+919876543210"
    assert normalize_phone("+1 (555) 123-4567") == "+15551234567"
    assert normalize_phone(None) is None
