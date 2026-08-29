import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.schema import Business, PipelineStage

@pytest.mark.asyncio
async def test_list_businesses_empty(auth_client: AsyncClient):
    res = await auth_client.get("/businesses")
    assert res.status_code == 200
    assert res.json() == []

@pytest.mark.asyncio
async def test_search_and_filter_businesses(auth_client: AsyncClient, db_session: AsyncSession):
    # Seed businesses
    b1 = Business(business_name="Smile Dental Clinic", category="Dentist", city="Ahmedabad", pipeline_stage=PipelineStage.LEAD)
    b2 = Business(business_name="Ahmedabad Eye Care", category="Optometrist", city="Ahmedabad", pipeline_stage=PipelineStage.CONTACTED)
    b3 = Business(business_name="Mumbai Ortho Center", category="Orthopedics", city="Mumbai", pipeline_stage=PipelineStage.LEAD)
    db_session.add_all([b1, b2, b3])
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
    b = Business(business_name="Apex Dental", category="Dentist", city="Ahmedabad", pipeline_stage=PipelineStage.LEAD)
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)

    res = await auth_client.patch(f"/businesses/{b.id}/stage", json={"stage": "proposal"})
    assert res.status_code == 200
    data = res.json()
    assert data["old_stage"].lower() == "lead"
    assert data["new_stage"].lower() == "proposal"

    # Verify update persisted
    get_res = await auth_client.get("/businesses")
    assert get_res.json()[0]["pipeline_stage"].lower() == "proposal"
