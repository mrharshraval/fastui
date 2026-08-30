import pytest
from unittest.mock import AsyncMock, patch

from schemas.discovery import DiscoveredLead, DiscoverySearchParams
from services.worker_client import WorkerClient


@pytest.mark.asyncio
async def test_worker_client_raises_when_url_empty():
    with patch("services.worker_client.settings.WORKER_URL", None):
        params = DiscoverySearchParams(target_audience="Dentist", location="Ahmedabad", limit=5)
        with pytest.raises(ValueError, match="WORKER_URL is not configured"):
            await WorkerClient.discover(params)


@pytest.mark.asyncio
async def test_worker_client_success():
    mock_lead = DiscoveredLead(
        name="Test Dental Clinic",
        category="Dentist",
        city="Ahmedabad",
        phone="+919876500000",
        website="https://testdental.com",
        source_platform="google_maps",
    )

    with patch("services.worker_client.settings.WORKER_URL", "http://worker:8001"), \
         patch("services.worker_client.settings.WORKER_TOKEN", "secret-token-123"):
        with patch("services.worker_client.httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: {"leads": [mock_lead.model_dump()], "count": 1},
                raise_for_status=lambda: None,
            )

            params = DiscoverySearchParams(target_audience="Dentist", location="Ahmedabad", limit=5)
            leads = await WorkerClient.discover(params)

            assert len(leads) == 1
            assert leads[0].name == "Test Dental Clinic"
            assert leads[0].phone == "+919876500000"

            # Check that X-Worker-Token was passed in headers
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["headers"].get("X-Worker-Token") == "secret-token-123"
