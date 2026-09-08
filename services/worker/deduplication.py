"""
FastUI Worker Deduplication
============================
In-memory deduplication helpers for merging leads from multiple sources
before returning them to the API. No database access — that is the API's job.

Rules:
1. Duplicate detection must NOT be based on business name alone.
2. Businesses with the same or similar names are treated as separate entities
   unless there is additional supporting evidence (address, phone, website,
   place ID, coordinates).
3. If names are identical but location or other identifiers indicate different
   businesses (e.g. different addresses, postal codes, phones, or coordinates),
   do not merge or remove them.
"""

import math
import re
from typing import Optional, Union
from urllib.parse import urlparse

from contracts import DiscoveredLead

GENERIC_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "youtube.com", "google.com", "maps.google.com", "justdial.com", "indiamart.com",
    "practo.com", "lybrate.com", "yelp.com", "yellowpages.com", "tripadvisor.com",
    "wikipedia.org", "pinterest.com", "reddit.com", "github.com",
}

STREET_ABBREVIATIONS = {
    r"\brd\b": "road",
    r"\bst\b": "street",
    r"\bln\b": "lane",
    r"\bave\b": "avenue",
    r"\bav\b": "avenue",
    r"\bblvd\b": "boulevard",
    r"\bflr\b": "floor",
    r"\bfl\b": "floor",
    r"\bste\b": "suite",
    r"\bsec\b": "sector",
    r"\bsect\b": "sector",
    r"\bblk\b": "block",
    r"\bno\b": "number",
    r"\bopp\b": "opposite",
    r"\bnear\b": "near",
    r"\bbldg\b": "building",
    r"\bplz\b": "plaza",
    r"\bcplx\b": "complex",
}


class LeadDeduplicator:
    """
    In-memory normalization and multi-identifier duplicate detection for cross-source aggregation.
    """

    @staticmethod
    def normalize_phone(phone: Optional[str], location: Optional[str] = None) -> Optional[str]:
        """
        Normalizes a phone number to canonical E.164-style format (+<digits>).
        Defaults 10-digit numbers to +91 (Indian) country code.
        """
        if not phone or not isinstance(phone, str):
            return None

        digits = re.sub(r"\D", "", phone)
        if not digits:
            return None

        if digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]

        if len(digits) == 10:
            return f"+91{digits}"
        return f"+{digits}"

    @staticmethod
    def normalize_website(website: Optional[str]) -> Optional[str]:
        """
        Normalizes a website URL to its canonical base hostname.
        Strips protocols, www, ports, paths, and query strings.
        """
        if not website or not isinstance(website, str):
            return None

        clean_web = website.strip().lower()
        if not clean_web.startswith(("http://", "https://")):
            clean_web = "http://" + clean_web

        try:
            parsed = urlparse(clean_web)
            hostname = parsed.hostname or ""
            hostname = re.sub(r"^www\.", "", hostname)
            return hostname.strip() if hostname.strip() else None
        except Exception:
            cleaned = re.sub(r"^https?://", "", website.lower().strip())
            cleaned = re.sub(r"^www\.", "", cleaned)
            cleaned = cleaned.split("/")[0].split("?")[0].split("#")[0].split(":")[0]
            return cleaned if cleaned else None

    @staticmethod
    def extract_postal_code(text: Optional[str]) -> Optional[str]:
        if not text or not isinstance(text, str):
            return None
        match = re.search(r"\b([1-9]\d{4,5})\b", text)
        return match.group(1) if match else None

    @classmethod
    def normalize_address(cls, address: Optional[str]) -> str:
        if not address or not isinstance(address, str):
            return ""
        addr = address.lower()
        addr = addr.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u200b', ' ')
        for pattern, replacement in STREET_ABBREVIATIONS.items():
            addr = re.sub(pattern, replacement, addr)
        addr = re.sub(r"[^\w\s]", " ", addr)
        return " ".join(addr.split())

    @classmethod
    def are_addresses_matching(
        cls,
        addr1: Optional[str],
        addr2: Optional[str],
        postal1: Optional[str] = None,
        postal2: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Optional[bool]:
        """
        Returns:
          True  -> Positive evidence that both represent the same physical address.
          False -> Conflicting evidence (different postal codes, conflicting house/sector numbers).
          None  -> Insufficient address information to decide.
        """
        p1 = postal1 or cls.extract_postal_code(addr1)
        p2 = postal2 or cls.extract_postal_code(addr2)

        if p1 and p2 and p1 != p2:
            return False

        n1 = cls.normalize_address(addr1)
        n2 = cls.normalize_address(addr2)

        if not n1 or not n2:
            return None

        if n1 == n2:
            return True

        noise = {"near", "opposite", "behind", "beside", "at", "in", "on", "the", "and", "of", "floor", "number"}
        tokens1 = {t for t in n1.split() if len(t) > 1 and t not in noise}
        tokens2 = {t for t in n2.split() if len(t) > 1 and t not in noise}

        # Remove city / common geographic tokens so they don't count as false street matches
        if city:
            city_tokens = {t for t in cls.normalize_address(city).split() if len(t) > 1}
            tokens1 = tokens1 - city_tokens
            tokens2 = tokens2 - city_tokens
        else:
            w1 = [w for w in n1.split() if w not in noise]
            w2 = [w for w in n2.split() if w not in noise]
            if len(w1) > 1 and len(w2) > 1 and w1[-1] == w2[-1]:
                tokens1.discard(w1[-1])
                tokens2.discard(w2[-1])

        if not tokens1 or not tokens2:
            return None

        common = tokens1 & tokens2

        # House / plot / sector numbers must not conflict
        nums1 = {t for t in tokens1 if t.isdigit()}
        nums2 = {t for t in tokens2 if t.isdigit()}
        if nums1 and nums2 and nums1 != nums2:
            return False

        min_len = min(len(tokens1), len(tokens2))
        overlap_ratio = len(common) / min_len if min_len > 0 else 0.0

        if p1 and p2 and p1 == p2:
            if len(common) >= 2 or overlap_ratio >= 0.5:
                return True
            if len(common) == 0:
                return False

        union = tokens1 | tokens2
        jaccard = len(common) / len(union) if union else 0.0

        if jaccard >= 0.5 or (len(common) >= 3 and overlap_ratio >= 0.6):
            return True

        if len(tokens1) >= 2 and len(tokens2) >= 2 and len(common) == 0:
            return False

        return None

    @staticmethod
    def are_coordinates_matching(
        lat1: Optional[float],
        lon1: Optional[float],
        lat2: Optional[float],
        lon2: Optional[float],
    ) -> Optional[bool]:
        """
        Computes geographic distance in meters.
        Returns:
          True  -> within ~120m (same physical location).
          False -> >= 350m (different physical locations).
          None  -> missing or invalid coordinates.
        """
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None
        try:
            l1, o1, l2, o2 = float(lat1), float(lon1), float(lat2), float(lon2)
        except (ValueError, TypeError):
            return None

        if (l1 == 0.0 and o1 == 0.0) or (l2 == 0.0 and o2 == 0.0):
            return None

        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(l1)
        phi2 = math.radians(l2)
        delta_phi = math.radians(l2 - l1)
        delta_lambda = math.radians(o2 - o1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        dist = R * c

        if dist <= 120.0:
            return True
        elif dist >= 350.0:
            return False
        return None

    @classmethod
    def is_duplicate_lead(cls, lead1: DiscoveredLead, lead2: DiscoveredLead) -> bool:
        """
        Determines whether two DiscoveredLead instances represent the same physical business.
        Duplicate detection must NOT be based on business name alone.
        """
        c1 = lead1.city.strip().lower() if lead1.city else None
        c2 = lead2.city.strip().lower() if lead2.city else None
        effective_city = lead1.city or lead2.city

        # 1. Google Place ID / external source place ID match (strongest identity)
        pid1 = getattr(lead1, "google_place_id", None) or lead1.source_place_id
        pid2 = getattr(lead2, "google_place_id", None) or lead2.source_place_id
        if pid1 and pid2 and pid1 == pid2:
            return True

        # 2. Direct verified Phone match
        p1 = cls.normalize_phone(lead1.phone)
        p2 = cls.normalize_phone(lead2.phone)
        if p1 and p2 and p1 == p2:
            # Check for hard location conflict (different postal codes or conflicting addresses)
            post_match = cls.are_addresses_matching(lead1.address, lead2.address, lead1.postal_code, lead2.postal_code, city=effective_city)
            if post_match is False:
                return False
            return True

        # 3. Canonical Website match (excluding generic platforms/directories)
        w1 = cls.normalize_website(lead1.website)
        w2 = cls.normalize_website(lead2.website)
        if w1 and w2 and w1 not in GENERIC_DOMAINS and w2 not in GENERIC_DOMAINS and w1 == w2:
            # Check for phone conflict
            if p1 and p2 and p1 != p2:
                return False
            # Check for address conflict
            addr_match = cls.are_addresses_matching(lead1.address, lead2.address, lead1.postal_code, lead2.postal_code, city=effective_city)
            if addr_match is False:
                return False
            return True

        # 4. Name comparison with REQUIRED supporting location/business metadata
        name1 = lead1.name.lower().strip() if lead1.name else ""
        name2 = lead2.name.lower().strip() if lead2.name else ""
        if not name1 or not name2 or name1 != name2:
            return False

        # Names are identical or highly similar:
        # A. Check for negative evidence (conflicts) first:
        # - Different cities (e.g. Kolkata vs Mumbai, ignoring formatting variations)
        if c1 and c2 and c1 not in c2 and c2 not in c1:
            return False

        # - Different non-empty phones
        if p1 and p2 and p1 != p2:
            return False

        # - Different non-generic websites
        if w1 and w2 and w1 not in GENERIC_DOMAINS and w2 not in GENERIC_DOMAINS and w1 != w2:
            return False

        # - Different non-empty place IDs on the same platform
        if pid1 and pid2 and pid1 != pid2 and lead1.source_platform == lead2.source_platform:
            return False

        # - Conflicting addresses / postal codes
        addr_match = cls.are_addresses_matching(lead1.address, lead2.address, lead1.postal_code, lead2.postal_code, city=effective_city)
        if addr_match is False:
            return False

        # - Conflicting coordinates (>= 350m apart)
        coord_match = cls.are_coordinates_matching(lead1.latitude, lead1.longitude, lead2.latitude, lead2.longitude)
        if coord_match is False:
            return False

        # B. Check for positive supporting evidence:
        # - Matching physical address
        if addr_match is True:
            return True

        # - Matching coordinates (within ~120m)
        if coord_match is True:
            return True

        # Without supporting location/business metadata, name alone is NEVER enough!
        return False


# Module-level convenience aliases
normalize_phone = LeadDeduplicator.normalize_phone
normalize_website = LeadDeduplicator.normalize_website
normalize_address = LeadDeduplicator.normalize_address
extract_postal_code = LeadDeduplicator.extract_postal_code
are_addresses_matching = LeadDeduplicator.are_addresses_matching
are_coordinates_matching = LeadDeduplicator.are_coordinates_matching
is_duplicate_lead = LeadDeduplicator.is_duplicate_lead
