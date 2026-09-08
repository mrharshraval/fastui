import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.deduplication import (
    normalize_phone,
    normalize_website,
    normalize_address,
    are_addresses_matching,
    are_coordinates_matching,
    is_duplicate,
    find_duplicate,
)
from models.schema import Business, BusinessSource


def test_normalize_phone():
    # India with and without leading 0
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("09876543210", location="Ahmedabad, Gujarat, India") == "+919876543210"
    assert normalize_phone("079 2640 1234", location="Ahmedabad, Gujarat, India") == "+917926401234"

    # UK, USA, UAE with leading domestic 0
    assert normalize_phone("+1 (415) 555-1234") == "+14155551234"
    assert normalize_phone("020 7946 0919", location="London, UK") == "+442079460919"
    assert normalize_phone("04 123 4567", location="Dubai, UAE") == "+97141234567"
    assert normalize_phone(None) is None
    assert normalize_phone("") is None


def test_normalize_website():
    assert normalize_website("https://www.example.com/search?q=1#top") == "example.com"
    assert normalize_website("http://sub.domain.co.in:8080/") == "sub.domain.co.in"
    assert normalize_website("example.com") == "example.com"
    assert normalize_website(None) is None


def test_are_addresses_matching():
    # Same physical address with abbreviations
    assert are_addresses_matching(
        "Shop 4, Sunrise Complex, Drive-in Road, Ahmedabad 380054",
        "Sunrise Complex, Drive-in Rd, Memnagar, Ahmedabad 380054"
    ) is True

    # Same address without postal code
    assert are_addresses_matching(
        "12 Park Street, Kolkata",
        "12 Park St, Kolkata"
    ) is True

    # Conflicting postal codes in same city
    assert are_addresses_matching(
        "12 Park Street, Kolkata 700016",
        "Block CJ 241, Sector II, Salt Lake, Kolkata 700091"
    ) is False

    # Conflicting street numbers in same city
    assert are_addresses_matching(
        "12 Park Street, Kolkata",
        "50 Park Street, Kolkata"
    ) is False

    # Different localities with no overlap
    assert are_addresses_matching(
        "Park Street, Kolkata",
        "Salt Lake Sector V, Kolkata"
    ) is False

    # Insufficient data
    assert are_addresses_matching(None, "Park Street") is None
    assert are_addresses_matching(None, None) is None


def test_are_coordinates_matching():
    # Identical coordinates
    assert are_coordinates_matching(22.5726, 88.3639, 22.5726, 88.3639) is True

    # Very close (~50m apart)
    assert are_coordinates_matching(22.5726, 88.3639, 22.5730, 88.3639) is True

    # Far apart (~5km)
    assert are_coordinates_matching(22.5726, 88.3639, 22.6200, 88.4000) is False

    # Missing coordinates
    assert are_coordinates_matching(None, None, 22.5726, 88.3639) is None


@pytest.mark.asyncio
async def test_duplicate_detection_not_on_name_alone(db_session: AsyncSession):
    """
    Verifies that duplicate detection is NEVER based on name alone.
    Businesses with the same name are separate entities unless there is supporting evidence.
    """
    business = Business(
        business_name="Apex Dental Care",
        city="Kolkata",
        address="12 Park Street, Kolkata",
        postal_code="700016",
        phone="+919830000001",
        website="https://apexdentalcare.in",
        normalized_phone="+919830000001",
        normalized_website="apexdentalcare.in",
    )
    db_session.add(business)
    await db_session.commit()

    # 1. Match on website
    assert await is_duplicate(db_session, None, "apexdentalcare.in", "Other Name", "Other City") is True

    # 2. Match on phone
    assert await is_duplicate(db_session, "+919830000001", None, "Other Name", "Other City") is True

    # 3. CRITICAL: Same name and same city, but NO supporting identifiers -> MUST NOT be duplicate!
    assert await is_duplicate(db_session, None, None, "Apex Dental Care", "Kolkata") is False

    # 4. CRITICAL: Same name, same city, but DIFFERENT phone -> MUST NOT be duplicate!
    assert await is_duplicate(
        db_session,
        normalized_phone="+919830000099",
        normalized_website=None,
        business_name="Apex Dental Care",
        city="Kolkata"
    ) is False

    # 5. CRITICAL: Same name, same city, but DIFFERENT address / postal code -> MUST NOT be duplicate!
    assert await is_duplicate(
        db_session,
        normalized_phone=None,
        normalized_website=None,
        business_name="Apex Dental Care",
        city="Kolkata",
        address="Block CJ 241, Sector II, Salt Lake, Kolkata",
        postal_code="700091",
    ) is False

    # 6. Supporting address matches -> MUST be duplicate!
    assert await is_duplicate(
        db_session,
        normalized_phone=None,
        normalized_website=None,
        business_name="Apex Dental Care",
        city="Kolkata",
        address="12 Park St, Kolkata",
        postal_code="700016",
    ) is True

    # 7. CRITICAL: Same name, DIFFERENT city -> MUST NOT be duplicate!
    assert await is_duplicate(
        db_session,
        normalized_phone=None,
        normalized_website=None,
        business_name="Apex Dental Care",
        city="Mumbai",
    ) is False


@pytest.mark.asyncio
async def test_find_duplicate_with_place_id_and_sources(db_session: AsyncSession):
    """
    Tests finding duplicates via external Place ID and multi-source provenance.
    """
    biz = Business(
        business_name="Smile Dental Clinic",
        city="Kolkata",
        address="45 Southern Avenue, Kolkata",
        postal_code="700029",
    )
    db_session.add(biz)
    await db_session.flush()

    source = BusinessSource(
        business_id=biz.id,
        platform="google_maps",
        external_id="ChIJ_test_place_id_123",
    )
    db_session.add(source)
    await db_session.commit()

    # Match by Google Place ID even if phone/website are absent
    found = await find_duplicate(
        db_session,
        normalized_phone=None,
        normalized_website=None,
        business_name="Smile Dental Clinic",
        city="Kolkata",
        source_platform="google_maps",
        source_place_id="ChIJ_test_place_id_123",
    )
    assert found is not None
    assert found.id == biz.id

    # Same name but DIFFERENT Google Place ID -> separate entity (e.g. branch)
    found_diff = await find_duplicate(
        db_session,
        normalized_phone=None,
        normalized_website=None,
        business_name="Smile Dental Clinic",
        city="Kolkata",
        source_platform="google_maps",
        source_place_id="ChIJ_different_branch_456",
        address="100 Salt Lake, Kolkata",
        postal_code="700064",
    )
    assert found_diff is None

