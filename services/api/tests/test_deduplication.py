import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from worker.deduplication import normalize_phone, normalize_website, is_duplicate
from models.schema import Business, PipelineStage

def test_normalize_phone():
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("+1 (415) 555-1234") == "+14155551234"
    assert normalize_phone(None) is None
    assert normalize_phone("") is None

def test_normalize_website():
    assert normalize_website("https://www.example.com/search?q=1#top") == "example.com"
    assert normalize_website("http://sub.domain.co.in:8080/") == "sub.domain.co.in"
    assert normalize_website("example.com") == "example.com"
    assert normalize_website(None) is None

@pytest.mark.asyncio
async def test_is_duplicate(db_session: AsyncSession):
    business = Business(
        business_name="Unique Dental Clinic",
        city="Ahmedabad",
        phone="+919876500001",
        website="https://unique-dental.com",
        normalized_phone="+919876500001",
        normalized_website="unique-dental.com",
        pipeline_stage=PipelineStage.LEAD
    )
    db_session.add(business)
    await db_session.commit()

    # 1. Match on website
    assert await is_duplicate(db_session, None, "unique-dental.com", "Other Name", "Other City") is True

    # 2. Match on phone
    assert await is_duplicate(db_session, "+919876500001", None, "Other Name", "Other City") is True

    # 3. Match on exact name + city
    assert await is_duplicate(db_session, None, None, "Unique Dental Clinic", "Ahmedabad") is True

    # 4. No match on different business in same city
    assert await is_duplicate(db_session, "+919876599999", "newdomain.com", "Brand New Care", "Ahmedabad") is False
