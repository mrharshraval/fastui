import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.schema import Business, Lead, PipelineStage

@pytest.mark.asyncio
async def test_list_businesses_empty(auth_client: AsyncClient):
    res = await auth_client.get("/businesses")
    assert res.status_code == 200
    assert res.json() == []

@pytest.mark.asyncio
async def test_search_and_filter_businesses(auth_client: AsyncClient, db_session: AsyncSession):
    # Seed businesses with leads
    b1 = Business(business_name="Smile Dental Clinic", category="Dentist", city="Ahmedabad")
    b2 = Business(business_name="Ahmedabad Eye Care", category="Optometrist", city="Ahmedabad")
    b3 = Business(business_name="Mumbai Ortho Center", category="Orthopedics", city="Mumbai")
    db_session.add_all([b1, b2, b3])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)
    await db_session.refresh(b3)

    l1 = Lead(business_id=b1.id, stage=PipelineStage.LEAD)
    l2 = Lead(business_id=b2.id, stage=PipelineStage.CONTACTED)
    l3 = Lead(business_id=b3.id, stage=PipelineStage.LEAD)
    db_session.add_all([l1, l2, l3])
    await db_session.commit()

    # 1. Test search
    res = await auth_client.get("/businesses?search=Dental")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["business_name"] == "Smile Dental Clinic"

    # 2. Test stage filter
    res = await auth_client.get("/businesses?stage=lead")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # 3. Test sorting
    res = await auth_client.get("/businesses?sort_by=business_name&sort_order=asc")
    assert res.status_code == 200
    names = [b["business_name"] for b in res.json()]
    assert names == ["Ahmedabad Eye Care", "Mumbai Ortho Center", "Smile Dental Clinic"]

@pytest.mark.asyncio
async def test_update_pipeline_stage(auth_client: AsyncClient, db_session: AsyncSession):
    b = Business(business_name="Apex Dental", category="Dentist", city="Ahmedabad")
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)

    l = Lead(business_id=b.id, stage=PipelineStage.LEAD)
    db_session.add(l)
    await db_session.commit()

    res = await auth_client.patch(f"/businesses/{b.id}/stage", json={"stage": "proposal"})
    assert res.status_code == 200
    data = res.json()
    assert data["old_stage"].lower() == "lead"
    assert data["new_stage"].lower() == "proposal"

    # Verify update persisted
    get_res = await auth_client.get("/businesses")
    assert get_res.json()[0]["pipeline_stage"].lower() == "proposal"

@pytest.mark.asyncio
async def test_business_reminders_crud_and_timezone(auth_client: AsyncClient, db_session: AsyncSession):
    b = Business(business_name="Test Health Clinic", category="Clinic", city="Ahmedabad")
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)

    # 1. Create reminder with explicit UTC ISO timestamp
    payload = {
        "title": "Follow up on proposal",
        "notes": "Call Dr. Sharma",
        "due_at": "2026-09-02T20:50:08Z"
    }
    create_res = await auth_client.post(f"/businesses/{b.id}/reminders", json=payload)
    assert create_res.status_code == 200
    rem_data = create_res.json()
    assert rem_data["title"] == "Follow up on proposal"
    assert rem_data["business_id"] == b.id
    assert "+00:00" in rem_data["due_at"] or rem_data["due_at"].endswith("Z")

    # 2. Fetch business-specific reminders via GET /businesses/{id}/reminders
    list_res = await auth_client.get(f"/businesses/{b.id}/reminders")
    assert list_res.status_code == 200
    rems = list_res.json()
    assert len(rems) == 1
    assert rems[0]["title"] == "Follow up on proposal"
    assert "+00:00" in rems[0]["due_at"] or rems[0]["due_at"].endswith("Z")
    assert rems[0]["business_name"] == "Test Health Clinic"

    # 3. Update reminder due_at
    update_res = await auth_client.patch(
        f"/reminders/{rem_data['id']}",
        json={"due_at": "2026-09-05T14:30:00Z", "status": "completed"}
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"].lower() == "completed"
    assert "2026-09-05T14:30:00" in updated["due_at"]

