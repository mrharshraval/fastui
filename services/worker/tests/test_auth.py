import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from contracts import DiscoveredLead
from main import app


@pytest.mark.asyncio
async def test_health_endpoint_is_unauthenticated():
    """Confirms GET /health returns 200 without any authentication headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "fastui-worker"}


@pytest.mark.asyncio
async def test_discover_missing_token_returns_401():
    """Confirms POST /discover returns 401 when X-Worker-Token header is missing."""
    with patch("core.security.settings.WORKER_TOKEN", "secure-test-token-123"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {"target_audience": "Dentist", "location": "Ahmedabad", "limit": 5}
            resp = await client.post("/discover", json=payload)
            assert resp.status_code == 401
            assert "Missing" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_discover_invalid_token_returns_401():
    """Confirms POST /discover returns 401 when X-Worker-Token is incorrect."""
    with patch("core.security.settings.WORKER_TOKEN", "secure-test-token-123"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {"target_audience": "Dentist", "location": "Ahmedabad", "limit": 5}
            headers = {"X-Worker-Token": "wrong-token-xyz"}
            resp = await client.post("/discover", json=payload, headers=headers)
            assert resp.status_code == 401
            assert "Invalid" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_discover_valid_token_success():
    """Confirms POST /discover returns 200 when valid X-Worker-Token is provided."""
    mock_leads = [
        DiscoveredLead(
            name="Apex Dental Care",
            category="Dentist",
            city="Ahmedabad",
            phone="+919876543210",
            website="https://apexdental.example.com",
            source_platform="google_maps",
        )
    ]

    with patch("core.security.settings.WORKER_TOKEN", "secure-test-token-123"):
        with patch(
            "sources.aggregator.MultiSourceDiscoveryAggregator.discover",
            new_callable=AsyncMock,
        ) as mock_discover:
            mock_discover.return_value = mock_leads

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                payload = {"target_audience": "Dentist", "location": "Ahmedabad", "limit": 5}
                headers = {"X-Worker-Token": "secure-test-token-123"}
                resp = await client.post("/discover", json=payload, headers=headers)

                assert resp.status_code == 200
                data = resp.json()
                assert data["count"] == 1
                assert data["leads"][0]["name"] == "Apex Dental Care"


@pytest.mark.asyncio
async def test_discover_server_unconfigured_token_returns_401():
    """Confirms POST /discover returns 401 when the worker server has no WORKER_TOKEN set."""
    with patch("core.security.settings.WORKER_TOKEN", None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {"target_audience": "Dentist", "location": "Ahmedabad", "limit": 5}
            headers = {"X-Worker-Token": "some-token"}
            resp = await client.post("/discover", json=payload, headers=headers)
            assert resp.status_code == 401
            assert "not configured" in resp.json().get("detail", "")
