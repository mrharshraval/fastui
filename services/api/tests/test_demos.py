import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.schema import Business, BusinessSource, ProspectDemo

@pytest.mark.asyncio
async def test_prospect_demo_lifecycle(auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession):
    # 1. Create a test dental business
    business = Business(
        business_name="Smile Dental Studio",
        category="Dental Clinic",
        phone="+91 98765 43210",
        email="care@smiledental.com",
        address="402 Medical Square, Drive-In Road",
        city="Ahmedabad",
        state="Gujarat",
        has_whatsapp=True
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    # Attach a Google Maps source with place_id and rating
    source = BusinessSource(
        business_id=business.id,
        platform="google_maps",
        external_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
        raw_payload={"rating": 4.9, "reviews_count": 142, "opening_hours": "Mon-Sat: 9:00 AM - 8:00 PM"}
    )
    db_session.add(source)
    await db_session.commit()

    # 2. CRM Endpoint: Generate demo
    resp = await auth_client.post(f"/businesses/{business.id}/demo")
    assert resp.status_code == 200
    demo_data = resp.json()
    assert "token" in demo_data
    token = demo_data["token"]
    assert len(token) >= 24
    assert demo_data["demo_url"].endswith(f"/{token}")
    assert demo_data["view_count"] == 0

    # 3. CRM Endpoint: Fetch existing demo (idempotency check)
    fetch_resp = await auth_client.get(f"/businesses/{business.id}/demo")
    assert fetch_resp.status_code == 200
    assert fetch_resp.json()["token"] == token

    # 4. Public Endpoint: GET /public/v1/demos/{token} (Unauthenticated)
    pub_resp = await client.get(f"/public/v1/demos/{token}")
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()

    # Security check: 'token' MUST NOT be in public presentation payload
    assert "token" not in pub_data
    assert "lead_id" not in pub_data
    assert "score" not in pub_data
    assert "owner_id" not in pub_data

    # Presentation structure check
    assert pub_data["status"] == "active"
    assert pub_data["template_id"] == "dental-default"
    assert "business" in pub_data
    assert "customization" in pub_data

    biz_pres = pub_data["business"]
    assert biz_pres["name"] == "Smile Dental Studio"
    assert biz_pres["city"] == "Ahmedabad"
    assert biz_pres["rating"] == 4.9
    assert biz_pres["reviews_count"] == 142
    assert biz_pres["place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert biz_pres["whatsapp"] == "+91 98765 43210"

    # Cache Header check
    assert "Cache-Control" in pub_resp.headers
    assert "private" in pub_resp.headers["Cache-Control"]

    # 5. Public Endpoint: 404 for invalid token
    not_found_resp = await client.get("/public/v1/demos/non-existent-token-xyz")
    assert not_found_resp.status_code == 404

    # 6. Public Event Tracking: demo_viewed
    event_resp = await client.post(
        f"/public/v1/demos/{token}/events",
        json={
            "event_type": "demo_viewed",
            "session_id": "session-123",
            "page_path": "/"
        },
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    assert event_resp.status_code == 200
    assert event_resp.json()["status"] == "recorded"

    # Verify view count incremented in CRM
    crm_after_view = await auth_client.get(f"/businesses/{business.id}/demo")
    assert crm_after_view.json()["view_count"] == 1

    # 7. Deduplication within 15 minutes: Same session should NOT increment count again
    dup_event_resp = await client.post(
        f"/public/v1/demos/{token}/events",
        json={
            "event_type": "demo_viewed",
            "session_id": "session-123",
            "page_path": "/about"
        },
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    assert dup_event_resp.status_code == 200
    crm_after_dup = await auth_client.get(f"/businesses/{business.id}/demo")
    assert crm_after_dup.json()["view_count"] == 1  # Still 1, deduplicated!

    # 8. Bot Filtering: WhatsApp crawler should be ignored
    bot_event_resp = await client.post(
        f"/public/v1/demos/{token}/events",
        json={
            "event_type": "demo_viewed",
            "session_id": "session-bot",
            "page_path": "/"
        },
        headers={"User-Agent": "WhatsApp/2.21.12.21 A"}
    )
    assert bot_event_resp.status_code == 200
    assert bot_event_resp.json()["status"] == "ignored_bot"
    crm_after_bot = await auth_client.get(f"/businesses/{business.id}/demo")
    assert crm_after_bot.json()["view_count"] == 1  # Bot did not increment!


@pytest.mark.asyncio
async def test_clinic_b_minimal_data(auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession):
    # Clinic B: Minimal Data - phone only, no Google Maps source, no address, no email
    business = Business(
        business_name="City Dental Care",
        category="Dental Clinic",
        phone="+91 91234 56789",
        city=None,
        has_whatsapp=True
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    # Generate demo
    resp = await auth_client.post(f"/businesses/{business.id}/demo")
    assert resp.status_code == 200
    token = resp.json()["token"]

    # Fetch public demo
    pub_resp = await client.get(f"/public/v1/demos/{token}")
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()

    biz = pub_data["business"]
    assert biz["name"] == "City Dental Care"
    assert biz["phone"] == "+91 91234 56789"
    assert biz["city"] is None
    assert biz["place_id"] is None
    # Fallback rating and reviews count
    assert biz["rating"] == 4.9
    assert biz["reviews_count"] == 120
    assert biz["opening_hours"] == "Mon-Sat: 9:00 AM - 8:00 PM"

    # Fallback subheadline should use 'our community' when city is missing
    cust = pub_data["customization"]
    assert "our community" in cust["hero_subheadline"]
    assert cust["doctor_name"] == "Dr. Sarah Jenkins"


@pytest.mark.asyncio
async def test_clinic_c_edge_case_no_phone(auth_client: AsyncClient, client: AsyncClient, db_session: AsyncSession):
    # Clinic C: Edge case - No phone, no WhatsApp, but has city
    business = Business(
        business_name="Modern Orthodontics",
        category="Orthodontics",
        phone=None,
        city="Mumbai",
        has_whatsapp=False
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    # Generate demo
    resp = await auth_client.post(f"/businesses/{business.id}/demo")
    assert resp.status_code == 200
    token = resp.json()["token"]

    # Fetch public demo
    pub_resp = await client.get(f"/public/v1/demos/{token}")
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()

    biz = pub_data["business"]
    assert biz["name"] == "Modern Orthodontics"
    assert biz["phone"] is None
    assert biz["whatsapp"] is None
    assert biz["city"] == "Mumbai"

    cust = pub_data["customization"]
    assert "Mumbai" in cust["hero_subheadline"]

    # Test event tracking for call_clicked or cta_clicked
    evt_resp = await client.post(
        f"/public/v1/demos/{token}/events",
        json={
            "event_type": "cta_clicked",
            "session_id": "session-c1",
            "page_path": "/book"
        },
        headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}
    )
    assert evt_resp.status_code == 200
    assert evt_resp.json()["status"] == "recorded"

