import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.schema import ExportJob, ExportStatus, Business, Lead, PipelineStage
from services.export_service import ExportService

@pytest.mark.asyncio
async def test_create_export_default(auth_client: AsyncClient):
    """Verifies default export creation returning 202 Accepted."""
    res = await auth_client.post("/v1/exports")
    assert res.status_code == 202
    data = res.json()
    assert "export_id" in data
    export_id = data["export_id"]

    # Check status
    status_res = await auth_client.get(f"/v1/exports/{export_id}")
    assert status_res.status_code == 200
    assert status_res.json()["id"] == export_id

@pytest.mark.asyncio
async def test_download_completed_export(auth_client: AsyncClient, db_session: AsyncSession):
    """Verifies downloading a completed export with UTF-8 BOM."""
    b = Business(business_name="Export Dental", category="Dentist", city="Ahmedabad")
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)

    export_job = ExportJob(
        id="test-uuid-1234",
        status=ExportStatus.COMPLETED,
        export_type="prospects",
        progress_percent=100
    )
    db_session.add(export_job)
    await db_session.commit()

    download_res = await auth_client.get("/v1/exports/test-uuid-1234/download")
    assert download_res.status_code == 200
    assert "text/csv" in download_res.headers["content-type"]
    assert "Export Dental" in download_res.text
    # Check UTF-8 BOM (\ufeff / \xef\xbb\xbf)
    assert download_res.content.startswith(b"\xef\xbb\xbf")

@pytest.mark.asyncio
async def test_export_selected_records(auth_client: AsyncClient, db_session: AsyncSession):
    """Verifies exporting only selected records by IDs."""
    b1 = Business(business_name="Selected Clinic 1", category="Dentist", city="Mumbai")
    b2 = Business(business_name="Unselected Clinic 2", category="Dentist", city="Delhi")
    db_session.add_all([b1, b2])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)

    res = await auth_client.post("/v1/exports", json={
        "export_type": "prospects",
        "scope": "selected",
        "record_ids": [b1.id]
    })
    assert res.status_code == 202
    export_id = res.json()["export_id"]

    # Run background processing directly
    await ExportService.process_export(export_id)

    # Check download
    download_res = await auth_client.get(f"/v1/exports/{export_id}/download")
    assert download_res.status_code == 200
    assert "Selected Clinic 1" in download_res.text
    assert "Unselected Clinic 2" not in download_res.text

@pytest.mark.asyncio
async def test_export_filtered_leads(auth_client: AsyncClient, db_session: AsyncSession):
    """Verifies exporting leads filtered by stage and search."""
    b1 = Business(business_name="Won Dental Care", category="Dentist", city="Pune")
    b2 = Business(business_name="Lost Medical Care", category="Clinic", city="Pune")
    db_session.add_all([b1, b2])
    await db_session.commit()
    await db_session.refresh(b1)
    await db_session.refresh(b2)

    l1 = Lead(business_id=b1.id, stage=PipelineStage.WON)
    l2 = Lead(business_id=b2.id, stage=PipelineStage.LOST)
    db_session.add_all([l1, l2])
    await db_session.commit()

    res = await auth_client.post("/v1/exports", json={
        "export_type": "leads",
        "scope": "filtered",
        "filters": {
            "stage": "won",
            "search": "Dental"
        }
    })
    assert res.status_code == 202
    export_id = res.json()["export_id"]

    await ExportService.process_export(export_id)

    download_res = await auth_client.get(f"/v1/exports/{export_id}/download")
    assert download_res.status_code == 200
    assert "Won Dental Care" in download_res.text
    assert "Lost Medical Care" not in download_res.text
    # Leads headers must contain Pipeline Stage and Priority
    assert "Pipeline Stage" in download_res.text
    assert "Priority" in download_res.text

@pytest.mark.asyncio
async def test_csv_injection_sanitization(auth_client: AsyncClient, db_session: AsyncSession):
    """Verifies that cells beginning with dangerous characters are prefixed with apostrophe."""
    malicious_name = "=cmd|' /C calc'!A0"
    b = Business(business_name=malicious_name, category="+malicious_category", phone="+91 99999 88888")
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)

    res = await auth_client.post("/v1/exports", json={
        "export_type": "prospects",
        "scope": "selected",
        "record_ids": [b.id]
    })
    assert res.status_code == 202
    export_id = res.json()["export_id"]
    await ExportService.process_export(export_id)

    download_res = await auth_client.get(f"/v1/exports/{export_id}/download")
    assert download_res.status_code == 200
    # Must be sanitized with leading apostrophe
    assert "'=cmd|' /C calc'!A0" in download_res.text
    assert "'+malicious_category" in download_res.text
    assert "'+91 99999 88888" in download_res.text

@pytest.mark.asyncio
async def test_export_empty_dataset(auth_client: AsyncClient):
    """Verifies exporting when no records match produces clean CSV with headers."""
    res = await auth_client.post("/v1/exports", json={
        "export_type": "prospects",
        "scope": "filtered",
        "filters": {
            "search": "NonExistentCompanyXYZ999"
        }
    })
    assert res.status_code == 202
    export_id = res.json()["export_id"]
    await ExportService.process_export(export_id)

    status_res = await auth_client.get(f"/v1/exports/{export_id}")
    assert status_res.json()["total_records"] == 0
    assert status_res.json()["status"] == "completed"

    download_res = await auth_client.get(f"/v1/exports/{export_id}/download")
    assert download_res.status_code == 200
    assert "Business Name" in download_res.text
