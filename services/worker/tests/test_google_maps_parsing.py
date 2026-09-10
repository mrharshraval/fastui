"""
Unit tests for Google Maps extraction functions and card parsing.
Verifies verified pin coordinates vs camera viewport rejection, canonical place ID and decimal CID extraction,
canonical place URL construction, locality decomposition, and card parsing.
"""

from pathlib import Path
from bs4 import BeautifulSoup
import pytest

from sources.google_maps import (
    extract_place_id,
    extract_decimal_cid,
    build_canonical_place_url,
    extract_coordinates,
    extract_phone_number,
    clean_unicode_spaces,
)
from geo.localities import resolve_city_localities

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
    url_viewport_only = "https://www.google.com/maps/place/Apex+Dental/@23.033812,72.585034,15z/data=!4m6!3m5"
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
    url_name_only = "https://www.google.com/maps/place/Smile+Care+Dental+Studio/@23.0338,72.5850,15z"
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


def test_resolve_city_localities():
    # 1. Dynamic OSM resolution for Ahmedabad
    locs_ahmedabad = resolve_city_localities("Ahmedabad, Gujarat, India")
    assert len(locs_ahmedabad) >= 10
    # Dynamic OSM includes areas like Naroda, Sahijpur, etc.
    assert any("naroda" in loc.lower() or "paldi" in loc.lower() or "maninagar" in loc.lower() for loc in locs_ahmedabad)

    # 2. Dynamic OSM resolution for Mumbai
    locs_mumbai = resolve_city_localities("Mumbai, Maharashtra")
    assert len(locs_mumbai) >= 10

    # 3. Dynamic OSM resolution for other cities
    locs_other = resolve_city_localities("Gandhinagar, Gujarat")
    assert len(locs_other) >= 5


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

    from utils.phone import is_mobile_phone, get_whatsapp_url
    assert is_mobile_phone(phone, location="Ahmedabad, Gujarat, India") is True
    assert get_whatsapp_url(phone, location="Ahmedabad, Gujarat, India") == "https://wa.me/919825158578"


def test_extract_phone_number_does_not_raise_name_error():
    card_text = "Dr. Mehta Clinic 094995 57474 Dental clinic"
    phone = extract_phone_number(card_text, location="Kolkata, India")
    assert phone == "+91 94995 57474"


def test_dynamic_locality_resolver_caching():
    from geo.localities import DynamicLocalityResolver
    resolver = DynamicLocalityResolver()
    resolver._memory_cache["testcity"] = ["Area A", "Area B", "Area C"]
    result = resolver.resolve("testcity, State, Country")
    assert result == ["Area A", "Area B", "Area C"]


def test_dynamic_locality_resolver_fallback_on_network_error():
    from unittest.mock import patch
    from geo.localities import DynamicLocalityResolver
    resolver = DynamicLocalityResolver()
    resolver._memory_cache.pop("mumbai", None)
    
    with patch.object(resolver, "fetch_nominatim_iterative", side_effect=RuntimeError("Network down")), \
         patch.object(resolver, "fetch_overpass", return_value=[]):
        locs = resolver.resolve("Mumbai, Maharashtra, India")
        # Gracefully falls back to curated registry
        assert "Bandra West" in locs
        assert "Andheri West" in locs


def test_dynamic_locality_resolver_directional_fallback_for_unlisted():
    from unittest.mock import patch
    from geo.localities import DynamicLocalityResolver
    resolver = DynamicLocalityResolver()
    resolver._memory_cache.pop("marsopolis", None)
    
    with patch.object(resolver, "fetch_nominatim_iterative", return_value=[]), \
         patch.object(resolver, "fetch_overpass", return_value=[]):
        locs = resolver.resolve("Marsopolis, OuterSpace")
        assert "Central Marsopolis" in locs
        assert "North Marsopolis" in locs
        assert "South Marsopolis" in locs


def test_dynamic_locality_resolver_subdivision_of_dense_areas():
    from geo.localities import DynamicLocalityResolver
    resolver = DynamicLocalityResolver()
    areas = ["Ring Road", "Tech Square", "Quiet Village"]
    subdivided = resolver.subdivide_dense_areas(areas, "SampleCity")
    assert "Ring Road" in subdivided
    assert "Ring Road East" in subdivided
    assert "Ring Road West" in subdivided
    assert "Tech Square East" in subdivided
    assert "Quiet Village" in subdivided
    assert "Quiet Village East" not in subdivided

