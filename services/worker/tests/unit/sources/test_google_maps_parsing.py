"""
Unit tests for Google Maps extraction functions and card parsing.
Verifies verified pin coordinates vs camera viewport rejection, canonical place ID and decimal CID extraction,
canonical place URL construction, locality decomposition, and card parsing.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from geo.localities import resolve_city_localities
from sources.google_maps import (
    build_canonical_place_url,
    extract_coordinates,
    extract_decimal_cid,
    extract_phone_number,
    extract_place_id,
)

FIXTURES_DIR = next((p / "fixtures" for p in Path(__file__).resolve().parents if (p / "fixtures").is_dir()), Path(__file__).parent / "fixtures")


def test_extract_coordinates_verified_pin_patterns():
    # 1. Standard !8m2!3d and !4d pin coordinates in place URL
    url_8m2 = "https://www.google.com/maps/place/Apex+Dental/@23.033812,72.585034,15z/data=!4m6!3m5!1s0x395e84f123456789:0x8776dc6d5b0665f8!8m2!3d23.033812!4d72.585034"
    lat, lng = extract_coordinates(url_8m2)
    assert lat == 23.033812
    assert lng == 72.585034

    # 2. Direct !3d and !4d pin coordinates
    url_3d4d = "https://www.google.com/maps/place/Dental+Care/data=!3d28.613939!4d77.209021"
    lat2, lng2 = extract_coordinates(url_3d4d)
    assert lat2 == 28.613939
    assert lng2 == 77.209021


def test_extract_coordinates_rejects_viewport_and_search_urls():
    # Unverified camera viewport (/@lat,lng) without a pin is strictly rejected
    url_viewport_only = (
        "https://www.google.com/maps/place/Apex+Dental/@23.033812,72.585034,15z/data=!4m6!3m5"
    )
    assert extract_coordinates(url_viewport_only) == (None, None)

    # Pure search URLs are strictly rejected to prevent viewport collision
    search_url = "https://www.google.com/maps/search/dentist/data=!3d28.613939!4d77.209021"
    assert extract_coordinates(search_url) == (None, None)

    # Invalid coordinates / None
    assert extract_coordinates(None) == (None, None)
    assert extract_coordinates("https://www.google.com/maps/search/dentist") == (None, None)
    assert extract_coordinates("https://www.google.com/maps/@95.000,200.000,15z") == (None, None)


def test_extract_place_id_hex_and_chij():
    # 1. Canonical hex token
    url_hex = "https://www.google.com/maps/data=!1s0x395e84f123456789:0x8776dc6d5b0665f8!8m2"
    assert extract_place_id(url_hex) == "0x395e84f123456789:0x8776dc6d5b0665f8"

    # 2. ChIJ Place ID
    url_chij = "https://www.google.com/maps/place/data=!1sChIJN1t_tDeuEmsRUsoyG83frY4"
    assert extract_place_id(url_chij) == "ChIJN1t_tDeuEmsRUsoyG83frY4"

    # 3. Card attribute fallback
    card_attrs = {"data-result-id": "0x395e84f000000000:0x1111111111111111"}
    assert extract_place_id(None, card_attrs=card_attrs) == "0x395e84f000000000:0x1111111111111111"


def test_extract_place_id_never_returns_business_name():
    # URL has place name in path but no valid place ID pattern
    url_name_only = (
        "https://www.google.com/maps/place/Smile+Care+Dental+Studio/@23.0338,72.5850,15z"
    )
    # MUST return None, NEVER "Smile Care Dental Studio"!
    assert extract_place_id(url_name_only) is None


def test_extract_decimal_cid():
    # 1. Secondary hex token from URL -> decimal integer string
    url = "https://www.google.com/maps/data=!1s0x395e848aba5bd449:0x4fc14db35ff0a388!8m2"
    cid = extract_decimal_cid(url)
    assert cid == str(int("0x4fc14db35ff0a388", 16))
    assert cid == "5746960032305554312"

    # 2. URL already containing ?cid=...
    url_cid = "https://www.google.com/maps?cid=5746960032305554312"
    assert extract_decimal_cid(url_cid) == "5746960032305554312"

    # 3. Standalone 0x:0x token
    token = "0x395e84f123456789:0x8776dc6d5b0665f8"
    assert extract_decimal_cid(token) == str(int("0x8776dc6d5b0665f8", 16))


def test_build_canonical_place_url():
    # 1. Place URL with hex token -> generates authoritative CID URL
    url_hex = "https://www.google.com/maps/place/Apex/@23.0,72.0/data=!1s0x395e848aba5bd449:0x4fc14db35ff0a388!8m2"
    canonical = build_canonical_place_url(url_hex)
    assert canonical == "https://www.google.com/maps?cid=5746960032305554312"

    # 2. Place URL without hex -> generates clean /maps/place/ URL
    url_place = "https://www.google.com/maps/place/Apex+Dental+Clinic/@23.0,72.0?entry=ttu"
    canonical2 = build_canonical_place_url(url_place)
    assert canonical2 == "https://www.google.com/maps/place/Apex+Dental+Clinic/@23.0,72.0"

    # 3. Strictly rejects search query URLs (returns None)
    search_url = "https://www.google.com/maps/search/dentist+in+ahmedabad"
    assert build_canonical_place_url(search_url) is None

    # 4. None / empty handling
    assert build_canonical_place_url(None) is None
    assert build_canonical_place_url("") is None


@pytest.mark.asyncio
async def test_resolve_city_localities():
    from unittest.mock import AsyncMock, patch

    with patch("geo.localities.get_default_resolver") as mock_get_resolver:
        mock_resolver = AsyncMock()
        mock_resolver.resolve.return_value = [
            "Navrangpura",
            "Satellite",
            "Bodakdev",
            "Paldi",
            "Maninagar",
        ]
        mock_get_resolver.return_value = mock_resolver

        locs = await resolve_city_localities("Ahmedabad, Gujarat, India")
        assert len(locs) == 5
        assert "Paldi" in locs
        assert "Maninagar" in locs


def test_parse_google_maps_dental_cards_fixture():
    fixture_path = FIXTURES_DIR / "google_maps_dental_cards.html"
    assert fixture_path.exists()

    with open(fixture_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    cards = soup.find_all("div", class_="Nv2PK")
    assert len(cards) == 2

    # Card 1 assertions (complete with true pin coordinates)
    c1 = cards[0]
    c1_name = c1.find("div", class_="fontHeadlineSmall").get_text(strip=True)
    assert c1_name == "Apex Dental Clinic"

    c1_rating = float(c1.find("span", class_="MW4etd").get_text(strip=True))
    assert c1_rating == 4.8

    c1_reviews = int(c1.find("span", class_="UY7F9").get_text(strip=True).strip("()"))
    assert c1_reviews == 347

    c1_href = c1.find("a", class_="hfpxzc")["href"]
    lat, lng = extract_coordinates(c1_href)
    assert lat == 23.033812
    assert lng == 72.585034

    place_id = extract_place_id(c1_href, card_attrs={"data-result-id": c1.get("data-result-id")})
    assert place_id == "0x395e84f123456789:0x8776dc6d5b0665f8"

    # Decimal CID derivation
    decimal_cid = extract_decimal_cid(c1_href)
    assert decimal_cid == str(int("0x8776dc6d5b0665f8", 16))

    # Canonical place URL
    canonical_url = build_canonical_place_url(c1_href)
    assert canonical_url == f"https://www.google.com/maps?cid={decimal_cid}"

    # Card 2 assertions (minimal, only has viewport camera center, so pin coordinates are None)
    c2 = cards[1]
    c2_name = c2.find("div", class_="qBF1Pd").get_text(strip=True)
    assert c2_name == "City Smile Orthodontics"

    c2_rating = float(c2.find("span", class_="MW4etd").get_text(strip=True))
    assert c2_rating == 4.6

    c2_href = c2.find("a", class_="hfpxzc")["href"]
    place_id_2 = extract_place_id(c2_href)
    assert place_id_2 == "ChIJN1t_tDeuEmsRUsoyG83frY4"

    lat2, lng2 = extract_coordinates(c2_href)
    assert lat2 is None
    assert lng2 is None


def test_extract_phone_number_and_whatsapp():
    text_with_phone = "Apex Dental Clinic · Dental clinic · 098251 58578 · Open ⋅ Closes 8 pm"
    phone = extract_phone_number(text_with_phone, location="Ahmedabad, Gujarat, India")
    assert phone == "+91 98251 58578"

    from shared.phone import get_whatsapp_url, is_mobile_phone

    assert is_mobile_phone(phone, location="Ahmedabad, Gujarat, India") is True
    assert (
        get_whatsapp_url(phone, location="Ahmedabad, Gujarat, India")
        == "https://wa.me/919825158578"
    )


def test_extract_phone_number_does_not_raise_name_error():
    card_text = "Dr. Mehta Clinic 094995 57474 Dental clinic"
    phone = extract_phone_number(card_text, location="Kolkata, India")
    assert phone == "+91 94995 57474"


@pytest.mark.asyncio
async def test_dynamic_locality_resolver_caching():
    from geo.caching import LocalityCache
    from geo.models import Locality
    from geo.resolver import DynamicLocalityResolver

    cache = LocalityCache()
    cache.set(
        "testcity",
        [
            Locality(name="Area A", city="testcity"),
            Locality(name="Area B", city="testcity"),
            Locality(name="Area C", city="testcity"),
        ],
    )
    resolver = DynamicLocalityResolver(providers=[], cache=cache)
    result = await resolver.resolve("testcity, State, Country")
    assert result == ["Area A", "Area B", "Area C"]


@pytest.mark.asyncio
async def test_dynamic_locality_resolver_provider_fallback_on_network_error():
    from unittest.mock import AsyncMock

    from geo.models import Locality
    from geo.resolver import DynamicLocalityResolver

    failing_provider = AsyncMock()
    failing_provider.provider_name = "failing"
    failing_provider.fetch_localities.side_effect = RuntimeError("Network down")

    healthy_provider = AsyncMock()
    healthy_provider.provider_name = "healthy"
    healthy_provider.fetch_localities.return_value = [
        Locality(name="Bandra West", city="Mumbai"),
        Locality(name="Andheri West", city="Mumbai"),
    ]

    resolver = DynamicLocalityResolver(providers=[failing_provider, healthy_provider])
    locs = await resolver.resolve("Mumbai, Maharashtra, India")
    assert "Bandra West" in locs
    assert "Andheri West" in locs


@pytest.mark.asyncio
async def test_dynamic_locality_resolver_never_fabricates_synthetic_sectors():
    from unittest.mock import AsyncMock

    from geo.resolver import DynamicLocalityResolver

    empty_provider = AsyncMock()
    empty_provider.provider_name = "osm"
    empty_provider.fetch_localities.return_value = []

    resolver = DynamicLocalityResolver(providers=[empty_provider])
    locs = await resolver.resolve("Marsopolis, OuterSpace")
    # Strictly returns empty list: zero fabricated "Central Marsopolis" or "North Marsopolis"
    assert locs == []
    assert not any("north" in x.lower() or "central" in x.lower() for x in locs)


@pytest.mark.asyncio
async def test_dynamic_locality_resolver_deduplication():
    from unittest.mock import AsyncMock

    from geo.models import Locality
    from geo.resolver import DynamicLocalityResolver

    p1 = AsyncMock()
    p1.provider_name = "p1"
    p1.fetch_localities.return_value = [
        Locality(name="Tech Square", city="SampleCity"),
        Locality(name="Ring Road", city="SampleCity"),
    ]

    p2 = AsyncMock()
    p2.provider_name = "p2"
    p2.fetch_localities.return_value = [
        Locality(name="ring road", city="SampleCity"),  # case-insensitive duplicate
        Locality(name="Quiet Village", city="SampleCity"),
    ]

    resolver = DynamicLocalityResolver(providers=[p1, p2])
    results = await resolver.resolve("SampleCity")
    assert len(results) == 3
    assert results == ["Tech Square", "Ring Road", "Quiet Village"]
