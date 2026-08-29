import pytest
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.schema import DiscoveryJob, JobStatus

@pytest.mark.asyncio
async def test_create_and_poll_discovery_job(auth_client: AsyncClient):
    payload = {
        "business_type": "Dentist",
        "location": {"city": "Ahmedabad", "state": "Gujarat", "country": "India"},
        "website_status": "any"
    }
    
    with patch("services.discovery_service.DiscoveryService.process_job"):
        create_res = await auth_client.post("/prospecting/jobs", json=payload)
        assert create_res.status_code == 200
        data = create_res.json()
        assert "job_id" in data
        job_id = int(data["job_id"])

        # Poll status
        status_res = await auth_client.get(f"/prospecting/jobs/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["job_id"] == str(job_id)

@pytest.mark.asyncio
async def test_cancel_discovery_job(auth_client: AsyncClient, db_session: AsyncSession):
    job = DiscoveryJob(
        query={"business_type": "Plumber", "location": {"city": "Mumbai"}},
        status=JobStatus.QUEUED
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    cancel_res = await auth_client.patch(f"/prospecting/jobs/{job.id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
