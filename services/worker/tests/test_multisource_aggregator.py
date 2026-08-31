"""
FastUI Worker MultiSource Aggregator Tests
==========================================
Tests source orchestration, priority, failure isolation, and per-source exhaustion.
"""

from unittest.mock import AsyncMock, patch
import pytest

from contracts import DiscoveredLead, DiscoverySearchParams
from sources.aggregator import MultiSourceDiscoveryAggregator


@pytest.mark.asyncio
async def test_multisource_orchestration_and_enrichment():
    aggregator = MultiSourceDiscoveryAggregator(headless=True)

    lead_maps = DiscoveredLead(
        name="Apollo Dental",
        category="Dentist",
        city="Kolkata",
        phone="+919830000001",
        website=None,
        source_platform="google_maps",
        source_place_id="place_123",
    )
    lead_web = DiscoveredLead(
        name="Apollo Dental",
        category="Dentist",
        city="Kolkata",
        phone=None,
        website="https://apollodental.com",
        email="info@apollodental.com",
        source_platform="web_search",
    )

    with patch.object(aggregator.google_maps, "discover", new_callable=AsyncMock) as mock_maps, \
         patch.object(aggregator.web_search, "discover", new_callable=AsyncMock) as mock_web:
        mock_maps.return_value = [lead_maps]
        mock_web.return_value = [lead_web]

        params = DiscoverySearchParams(target_audience="Dentist", location="Kolkata", limit=50)
        leads = await aggregator.discover(params)

        assert len(leads) == 1
        enriched = leads[0]
        assert enriched.name == "Apollo Dental"
        assert enriched.phone == "+919830000001"
        assert enriched.website == "https://apollodental.com"
        assert enriched.email == "info@apollodental.com"
        assert enriched.source_place_id == "place_123"


@pytest.mark.asyncio
async def test_multisource_failure_isolation():
    aggregator = MultiSourceDiscoveryAggregator(headless=True)

    lead_web = DiscoveredLead(
        name="City Dental Clinic",
        category="Dentist",
        city="Kolkata",
        phone="+919830000002",
        website="https://citydental.com",
        source_platform="web_search",
    )

    # Google Maps fails, Web Search succeeds
    with patch.object(aggregator.google_maps, "discover", side_effect=RuntimeError("Maps timeout")), \
         patch.object(aggregator.web_search, "discover", new_callable=AsyncMock) as mock_web:
        mock_web.return_value = [lead_web]

        params = DiscoverySearchParams(target_audience="Dentist", location="Kolkata", limit=50)
        leads = await aggregator.discover(params)

        assert len(leads) == 1
        assert leads[0].name == "City Dental Clinic"
        assert aggregator.sources_exhausted["google_maps"] is True


@pytest.mark.asyncio
async def test_multisource_exhaustion_detection():
    aggregator = MultiSourceDiscoveryAggregator(headless=True)

    with patch.object(aggregator.google_maps, "discover", new_callable=AsyncMock) as mock_maps, \
         patch.object(aggregator.web_search, "discover", new_callable=AsyncMock) as mock_web:
        mock_maps.return_value = []
        aggregator.google_maps.is_exhausted = True
        mock_web.return_value = []
        aggregator.web_search.is_exhausted = True

        params = DiscoverySearchParams(target_audience="Dentist", location="Kolkata", limit=50)
        leads, exhausted, sources_ex, peak_rss = await aggregator.discover_with_meta(params)

        assert len(leads) == 0
        assert exhausted is True
        assert sources_ex["google_maps"] is True
        assert sources_ex["web_search"] is True
