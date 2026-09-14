"""
FastUI Domain Identity & Entity Resolution
==========================================
Pure business rules for identity matching and lead deduplication.
Ensures duplicate detection is NEVER based on business name alone.
Zero external framework or I/O dependencies.
"""

import math
import re
from typing import List, Optional

from contracts.discovery import DiscoveredLead
from domain.normalization import normalize_address, normalize_business_name, normalize_website
from shared.phone import normalize_global_phone

GENERIC_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "youtube.com", "google.com", "maps.google.com", "justdial.com", "indiamart.com",
    "practo.com", "lybrate.com", "yelp.com", "yellowpages.com", "tripadvisor.com",
    "wikipedia.org", "pinterest.com", "reddit.com", "github.com",
}


def extract_postal_code(text: str | None) -> Optional[str]:
    """Extracts 5-6 digit postal code from address string."""
    if not text or not isinstance(text, str):
        return None
    match = re.search(r"\b(\d{5,6})\b", text)
    return match.group(1) if match else None


def are_addresses_matching(
    addr1: Optional[str],
    addr2: Optional[str],
    city: Optional[str] = None,
    postal1: Optional[str] = None,
    postal2: Optional[str] = None,
) -> bool:
    """Evaluates whether two address strings represent the same physical establishment."""
    if not addr1 or not addr2:
        return False

    pin1 = postal1 or extract_postal_code(addr1)
    pin2 = postal2 or extract_postal_code(addr2)
    if pin1 and pin2 and pin1 != pin2:
        return False

    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    if not norm1 or not norm2:
        return False

    if norm1 == norm2:
        return True

    # Check conflicting house/street numbers at beginning
    m1 = re.match(r"^(\d+)\b", norm1)
    m2 = re.match(r"^(\d+)\b", norm2)
    if m1 and m2 and m1.group(1) != m2.group(1):
        return False

    words1 = set(norm1.split())
    words2 = set(norm2.split())
    if not words1 or not words2:
        return False

    intersection = words1.intersection(words2)
    smaller_len = min(len(words1), len(words2))
    if smaller_len == 0:
        return False

    return (len(intersection) / smaller_len) >= 0.8


def are_coordinates_matching(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
    threshold_meters: float = 350.0,
) -> Optional[bool]:
    """Determines if two geographical points fall within a strict distance threshold."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c

    return distance <= threshold_meters


def same_business(a: DiscoveredLead, b: DiscoveredLead) -> bool:
    """
    Pure identity rule: Determines if lead `a` and lead `b` represent the exact same entity.
    Never relies on business name alone.
    """
    # 1. Exact Source Place ID Match
    place_a = a.google_place_id or a.source_place_id
    place_b = b.google_place_id or b.source_place_id
    if place_a and place_b and place_a == place_b:
        return True

    # 2. Normalized E.164 Phone Match
    _, phone_a = normalize_global_phone(a.phone, location=a.city or a.address)
    _, phone_b = normalize_global_phone(b.phone, location=b.city or b.address)
    if phone_a and phone_b and phone_a == phone_b:
        return True

    # 3. Canonical Website Domain Match (excluding generic portals/directories)
    web_a = normalize_website(a.website)
    web_b = normalize_website(b.website)
    if web_a and web_b and web_a not in GENERIC_DOMAINS and web_b not in GENERIC_DOMAINS:
        if web_a == web_b:
            return True

    # 4. Strict Physical Address & Coordinates Co-location with Name Similarity
    norm_a = a.normalized_name or (normalize_business_name(a.name).normalized_name if a.name else None)
    norm_b = b.normalized_name or (normalize_business_name(b.name).normalized_name if b.name else None)
    if norm_a and norm_b and norm_a == norm_b:
        city = a.city or b.city
        p1 = a.postal_code
        p2 = b.postal_code
        if are_addresses_matching(a.address, b.address, city=city, postal1=p1, postal2=p2):
            return True
        if are_coordinates_matching(a.latitude, a.longitude, b.latitude, b.longitude):
            return True

    return False


def is_duplicate_candidate(lead: DiscoveredLead, existing_leads: List[DiscoveredLead]) -> bool:
    """Checks if lead already exists in a given list of candidates."""
    for existing in existing_leads:
        if same_business(lead, existing):
            return True
    return False

