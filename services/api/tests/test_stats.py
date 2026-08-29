import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.schema import Business, Activity, ActivityType, PipelineStage

@pytest.mark.asyncio
async def test_dashboard_stats(auth_client: AsyncClient, db_session: AsyncSession):
    # Seed businesses with different stages
    b1 = Business(business_name="Stage Lead Care", category="Dentist", city="Ahmedabad", pipeline_stage=PipelineStage.LEAD)
    b2 = Business(business_name="Stage Proposal Clinic", category="Dentist", city="Ahmedabad", pipeline_stage=PipelineStage.PROPOSAL)
    db_session.add_all([b1, b2])
    await db_session.commit()
    await db_session.refresh(b1)

    # Seed activity
    act = Activity(business_id=b1.id, type=ActivityType.CALL_INITIATED, outcome="Scheduled consultation")
    db_session.add(act)
    await db_session.commit()

    res = await auth_client.get("/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["new_leads"] == 1
    assert data["proposals_sent"] == 1
    assert len(data["recent_activities"]) >= 1
