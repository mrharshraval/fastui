"""
Unit tests for Google Maps extraction functions and card parsing.
Verifies rating, review count, coordinates, Place ID, category, and address heuristics.
"""

from pathlib import Path
from bs4 import BeautifulSoup
import pytest

from sources.google_maps import (
    extract_place_id,
    extract_coordinates,
    extract_phone_number,
    clean_unicode_spaces,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_extract_coordinates_valid_url():
    url = "https://www.google.com/maps/place/Apex+Dental/@23.033812,72.585034,15z/data=!4m6!3m5"
    lat, lng = extract_coordinates(url)
    assert lat == 23.033812
    assert lng == 72.585034


def test_extract_coordinates_3d4d_pattern():
    url = "https://www.google.com/maps/search/dentist/data=!3d28.613939!4d77.209021"
    lat, lng = extract_coordinates(url)
    assert lat == 28.613939
    assert lng == 77.209021


def test_extract_coordinates_invalid_or_none():
    assert extract_coordinates(None) == (None, None)
    assert extract_coordinates("https://www.google.com/maps/search/dentist") == (None, None)
    # Range check failure
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


def test_parse_google_maps_dental_cards_fixture():
    fixture_path = FIXTURES_DIR / "google_maps_dental_cards.html"
    assert fixture_path.exists()

    with open(fixture_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    cards = soup.find_all("div", class_="Nv2PK")
    assert len(cards) == 2

    # Card 1 assertions
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

    # Card 2 assertions
    c2 = cards[1]
    c2_name = c2.find("div", class_="qBF1Pd").get_text(strip=True)
    assert c2_name == "City Smile Orthodontics"

    c2_rating = float(c2.find("span", class_="MW4etd").get_text(strip=True))
    assert c2_rating == 4.6

    c2_href = c2.find("a", class_="hfpxzc")["href"]
    place_id_2 = extract_place_id(c2_href)
    assert place_id_2 == "ChIJN1t_tDeuEmsRUsoyG83frY4"


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

