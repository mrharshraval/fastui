import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.schema import ExportJob, ExportStatus, Business, PipelineStage

@pytest.mark.asyncio
async def test_create_export(auth_client: AsyncClient):
    res = await auth_client.post("/exports/")
    assert res.status_code == 200
    data = res.json()
    assert "export_id" in data
    export_id = data["export_id"]

    # Check status
    status_res = await auth_client.get(f"/exports/{export_id}")
    assert status_res.status_code == 200
    assert status_res.json()["id"] == export_id

@pytest.mark.asyncio
async def test_download_completed_export(auth_client: AsyncClient, db_session: AsyncSession):
    # Seed business and completed export
    b = Business(business_name="Export Dental", category="Dentist", city="Ahmedabad", pipeline_stage=PipelineStage.LEAD)
    export_job = ExportJob(id="test-uuid-1234", status=ExportStatus.COMPLETED, progress_percent=100)
    db_session.add_all([b, export_job])
    await db_session.commit()

    download_res = await auth_client.get("/exports/test-uuid-1234/download")
    assert download_res.status_code == 200
    assert "text/csv" in download_res.headers["content-type"]
    assert "Export Dental" in download_res.text
