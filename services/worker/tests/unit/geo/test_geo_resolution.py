"""
Unit tests for the dynamic geo locality resolution system.
Validates validation rules, bounded caching, provider protocol compliance,
and resolution policy.
"""

import time
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from geo.caching import LocalityCache
from geo.models import Locality, LocalityType, LocationScope
from geo.providers.nominatim import NominatimProvider
from geo.providers.overpass import OverpassProvider
from geo.resolver import DynamicLocalityResolver
from geo.validation import (
    clean_city_name,
    clean_unicode_spaces,
    is_geographic_match,
    is_valid_locality_name,
    parse_location_scope,
)


def test_geo_validation_and_parsing():
    scope = parse_location_scope("Ahmedabad, Gujarat, India")
    assert scope.city == "Ahmedabad"
    assert scope.state == "Gujarat"
    assert scope.country == "India"

    scope_short = parse_location_scope("London, UK")
    assert scope_short.city == "London"
    assert scope_short.country == "UK"

    assert clean_unicode_spaces("  Area\u00a0\u200bOne  ") == "Area One"
    assert clean_city_name("Ahmedabad District") == "ahmedabad"
    assert clean_city_name("Mumbai City") == "mumbai"

    # Validation rules
    assert is_valid_locality_name("Navrangpura", "Ahmedabad") is True
    assert is_valid_locality_name("NH 48", "Ahmedabad") is False
    assert is_valid_locality_name("12", "Ahmedabad") is False
    assert is_valid_locality_name("ahmedabad", "Ahmedabad") is False


def test_is_geographic_match():
    display = "Bandra West, Mumbai, Maharashtra, India"
    address = {"city": "Mumbai", "country": "India"}
    assert is_geographic_match(display, address, "Mumbai", "India") is True

    # Mismatched city
    wrong_address = {"city": "Pune", "country": "India"}
    assert is_geographic_match("Shivajinagar, Pune", wrong_address, "Mumbai", "India") is False


def test_locality_cache_ttl_and_eviction():
    cache = LocalityCache(default_ttl_seconds=0.1, max_entries=2)
    locs = [Locality(name="Area 1", city="City")]

    cache.set("city_1", locs)
    assert cache.get("city_1") is not None

    # Test TTL expiration
    time.sleep(0.15)
    assert cache.get("city_1") is None

    # Test capacity eviction
    cache.set("a", locs, ttl_seconds=100)
    cache.set("b", locs, ttl_seconds=100)
    cache.set("c", locs, ttl_seconds=100)
    assert len(cache) <= 2


@pytest.mark.asyncio
async def test_nominatim_provider_parsing_and_filtering():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "name": "Bopal",
            "display_name": "Bopal, Ahmedabad, Gujarat, India",
            "lat": "23.03",
            "lon": "72.46",
            "address": {"city": "Ahmedabad", "country": "India"},
        },
        {
            # Should be rejected: outside target city
            "name": "Bhopal",
            "display_name": "Bhopal, Madhya Pradesh, India",
            "address": {"city": "Bhopal", "country": "India"},
        },
    ]
    mock_client.get.return_value = mock_response

    provider = NominatimProvider(client=mock_client, min_interval_sec=0.0)
    scope = LocationScope(raw_location="Ahmedabad, India", city="Ahmedabad", country="India")

    localities = await provider.fetch_localities(scope)
    assert len(localities) == 1
    assert localities[0].name == "Bopal"
    assert localities[0].locality_type == LocalityType.SUBURB


@pytest.mark.asyncio
async def test_overpass_provider_failover():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    # Mirror 1 fails with 504 Gateway Timeout, Mirror 2 succeeds
    fail_response = MagicMock()
    fail_response.status_code = 504

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "elements": [
            {
                "tags": {"name": "Satellite", "place": "suburb"},
                "lat": 23.03,
                "lon": 72.52,
            },
            {
                "tags": {"name": "Bodakdev", "place": "neighbourhood"},
                "lat": 23.04,
                "lon": 72.51,
            },
            {
                "tags": {"name": "Vastrapur", "place": "quarter"},
                "lat": 23.03,
                "lon": 72.53,
            },
            {
                "tags": {"name": "Prahlad Nagar", "place": "suburb"},
                "lat": 23.01,
                "lon": 72.50,
            },
            {
                "tags": {"name": "Thaltej", "place": "suburb"},
                "lat": 23.05,
                "lon": 72.51,
            },
        ]
    }
    mock_client.post.side_effect = [fail_response, success_response]

    provider = OverpassProvider(
        client=mock_client,
        mirrors=("https://mirror1.internal", "https://mirror2.internal"),
    )
    scope = LocationScope(raw_location="Ahmedabad", city="Ahmedabad")

    localities = await provider.fetch_localities(scope)
    assert len(localities) == 5
    names = [loc.name for loc in localities]
    assert "Satellite" in names
    assert "Thaltej" in names


@pytest.mark.asyncio
async def test_dynamic_resolver_context_management_and_aclose():
    mock_provider = AsyncMock()
    mock_provider.provider_name = "mock_p"
    mock_provider.aclose = AsyncMock()

    async with DynamicLocalityResolver(providers=[mock_provider]) as resolver:
        assert resolver is not None

    assert mock_provider.aclose.call_count == 1


def test_provider_reusable_across_different_event_loops():
    """Validates that NominatimProvider and OverpassProvider safely adapt when called in sequential event loops."""
    import asyncio

    nom = NominatimProvider()
    over = OverpassProvider()

    async def step1():
        c1 = await nom._get_client()
        l1 = nom._get_rate_lock()
        o1 = await over._get_client()
        assert not c1.is_closed
        assert not o1.is_closed
        return id(asyncio.get_running_loop())

    with asyncio.Runner() as runner:
        loop1_id = runner.run(step1())

    async def step2():
        c2 = await nom._get_client()
        l2 = nom._get_rate_lock()
        o2 = await over._get_client()
        assert not c2.is_closed
        assert not o2.is_closed
        # Must have recognized the new loop and created fresh clients/locks
        assert nom._client_loop is asyncio.get_running_loop()
        assert nom._rate_lock_loop is asyncio.get_running_loop()
        assert over._client_loop is asyncio.get_running_loop()
        return id(asyncio.get_running_loop())

    with asyncio.Runner() as runner:
        loop2_id = runner.run(step2())

    assert loop1_id != loop2_id
