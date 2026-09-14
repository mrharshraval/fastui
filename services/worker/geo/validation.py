"""
FastUI Geo Validation & Normalization
=====================================
Pure validation and parsing rules for geographic names, bounds, and settlement entities.
Zero external I/O or network dependencies.
"""

import re
from typing import Any, Dict, Optional

from geo.models import LocationScope

HIGHWAY_OR_CODE_PATTERN = re.compile(
    r"^(?:NH|SH|State Highway|National Highway|Expressway|Route|M\d+|A\d+|\d+)\b",
    re.IGNORECASE,
)
CITY_CLEANUP_REGEX = re.compile(r"\b(?:city|district|metro|area|region)\b", re.IGNORECASE)


def clean_unicode_spaces(text: str) -> str:
    """Collapses whitespace and normalizes non-breaking or zero-width spaces."""
    if not text or not isinstance(text, str):
        return ""
    cleaned = (
        text.replace("\u00a0", " ")
        .replace("\u200b", " ")
        .replace("\u202f", " ")
        .replace("\ufeff", " ")
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def clean_city_name(raw_city: str) -> str:
    """
    Normalizes a city string by removing administrative terms.
    Example: 'Ahmedabad City' -> 'ahmedabad'
    """
    if not raw_city:
        return ""
    cleaned = clean_unicode_spaces(raw_city).lower()
    cleaned = CITY_CLEANUP_REGEX.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_location_scope(location: str) -> LocationScope:
    """
    Parses a location string into structured city, state, and country components.
    Example: 'Ahmedabad, Gujarat, India' -> city='Ahmedabad', state='Gujarat', country='India'
    """
    raw = clean_unicode_spaces(location)
    parts = [clean_unicode_spaces(p) for p in raw.split(",") if clean_unicode_spaces(p)]

    if not parts:
        return LocationScope(raw_location="", city="")

    city = parts[0]
    state: Optional[str] = None
    country: Optional[str] = None

    if len(parts) == 2:
        country = parts[1]
    elif len(parts) >= 3:
        state = parts[1]
        country = parts[-1]

    return LocationScope(
        raw_location=raw,
        city=city,
        state=state,
        country=country,
    )


def is_valid_locality_name(name: str, target_city: str) -> bool:
    """
    Validates that an extracted locality name is a legitimate geographic area.
    Filters out numeric codes, single characters, highway labels, and duplicate city names.
    """
    cleaned = clean_unicode_spaces(name)
    if len(cleaned) < 3:
        return False

    # Filter out highway codes, pure numbers, and postal codes
    if HIGHWAY_OR_CODE_PATTERN.match(cleaned):
        return False

    if cleaned.isdigit():
        return False

    # Disallow exact case-insensitive match against target city name
    norm_name = clean_city_name(cleaned)
    norm_city = clean_city_name(target_city)
    if norm_name == norm_city:
        return False

    return True


def is_geographic_match(
    display_name: str,
    address: Dict[str, Any],
    target_city: str,
    target_country: Optional[str] = None,
) -> bool:
    """
    Strict geographic verification: ensures an entity returned from Nominatim/OSM
    actually falls within the target city boundary or district, not an unrelated region.
    """
    if not target_city:
        return True

    dn_lower = (display_name or "").lower()
    target_city_lower = clean_city_name(target_city)

    addr_city = (address.get("city") or "").lower()
    addr_town = (address.get("town") or "").lower()
    addr_district = (address.get("state_district") or "").lower()
    addr_county = (address.get("county") or "").lower()
    addr_state = (address.get("state") or "").lower()

    city_matched = (
        target_city_lower in dn_lower
        or target_city_lower in addr_city
        or target_city_lower in addr_town
        or target_city_lower in addr_district
        or target_city_lower in addr_county
        or target_city_lower in addr_state
    )

    if not city_matched:
        return False

    if target_country:
        target_country_lower = target_country.lower().strip()
        addr_country = (address.get("country") or "").lower()
        country_matched = (
            target_country_lower in dn_lower or target_country_lower in addr_country
        )
        if not country_matched:
            return False

    return True
