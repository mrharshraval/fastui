"""FastUI Lead Deduplication Service.

High-precision entity resolution and normalization rules for discovered business records.
Ensures duplicate detection is NEVER based on business name alone.
"""

import math
import re
from urllib.parse import urlparse

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.models import Business, BusinessSource
from app.shared.phone import normalize_global_phone

GENERIC_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "google.com",
    "maps.google.com",
    "justdial.com",
    "indiamart.com",
    "practo.com",
    "lybrate.com",
    "yelp.com",
    "yellowpages.com",
    "tripadvisor.com",
    "wikipedia.org",
    "pinterest.com",
    "reddit.com",
    "github.com",
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
    """Encapsulates phone, website, place ID, address, and physical entity deduplication algorithms."""

    @staticmethod
    def format_display_phone(phone: str | None, location: str | None = None) -> str | None:
        """Formats phone number for clean human display with universal country code."""
        display_phone, _ = normalize_global_phone(phone, location=location)
        return display_phone

    @staticmethod
    def normalize_phone(phone: str | None, location: str | None = None) -> str | None:
        """Normalizes a phone number to canonical E.164-style standard format (+<digits>)."""
        _, e164 = normalize_global_phone(phone, location=location)
        return e164

    @staticmethod
    def normalize_website(website: str | None) -> str | None:
        """Normalizes a website URL to its canonical base hostname."""
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
    def extract_postal_code(text: str | None) -> str | None:
        if not text or not isinstance(text, str):
            return None
        match = re.search(r"\b([1-9]\d{4,5})\b", text)
        return match.group(1) if match else None

    @classmethod
    def normalize_address(cls, address: str | None) -> str:
        if not address or not isinstance(address, str):
            return ""
        addr = address.lower()
        addr = addr.replace("\u202f", " ").replace("\xa0", " ").replace("\u200b", " ")
        for pattern, replacement in STREET_ABBREVIATIONS.items():
            addr = re.sub(pattern, replacement, addr)
        addr = re.sub(r"[^\w\s]", " ", addr)
        return " ".join(addr.split())

    @classmethod
    def are_addresses_matching(
        cls,
        addr1: str | None,
        addr2: str | None,
        postal1: str | None = None,
        postal2: str | None = None,
        city: str | None = None,
    ) -> bool | None:
        """Determines whether two addresses represent the same physical location."""
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

        noise = {
            "near",
            "opposite",
            "behind",
            "beside",
            "at",
            "in",
            "on",
            "the",
            "and",
            "of",
            "floor",
            "number",
        }
        tokens1 = {t for t in n1.split() if len(t) > 1 and t not in noise}
        tokens2 = {t for t in n2.split() if len(t) > 1 and t not in noise}

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
        lat1: float | None,
        lon1: float | None,
        lat2: float | None,
        lon2: float | None,
    ) -> bool | None:
        """Computes geographic distance in meters."""
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

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        dist = R * c

        if dist <= 120.0:
            return True
        elif dist >= 350.0:
            return False
        return None

    @classmethod
    async def find_duplicate(
        cls,
        session: AsyncSession,
        normalized_phone: str | None,
        normalized_website: str | None,
        business_name: str,
        city: str | None,
        source_platform: str | None = None,
        source_place_id: str | None = None,
        address: str | None = None,
        postal_code: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> Business | None:
        """Finds existing Business entity based on supporting identifiers."""
        # 1. Check BusinessSource external_id
        if source_platform and source_place_id:
            src_query = (
                select(Business)
                .join(BusinessSource, Business.id == BusinessSource.business_id)
                .where(
                    and_(
                        BusinessSource.platform == source_platform,
                        BusinessSource.external_id == source_place_id,
                    )
                )
                .limit(1)
            )
            src_res = await session.execute(src_query)
            existing_by_src = src_res.scalar_one_or_none()
            if existing_by_src:
                return existing_by_src

        # 2. Check normalized_phone
        if normalized_phone:
            phone_query = (
                select(Business).where(Business.normalized_phone == normalized_phone).limit(5)
            )
            phone_res = await session.execute(phone_query)
            phone_candidates = phone_res.scalars().all()
            for cand in phone_candidates:
                addr_match = cls.are_addresses_matching(
                    address, cand.address, postal_code, cand.postal_code, city=city or cand.city
                )
                if addr_match is False:
                    continue
                return cand

        # 3. Check normalized_website
        if normalized_website and normalized_website not in GENERIC_DOMAINS:
            web_query = (
                select(Business).where(Business.normalized_website == normalized_website).limit(5)
            )
            web_res = await session.execute(web_query)
            web_candidates = web_res.scalars().all()
            for cand in web_candidates:
                if (
                    normalized_phone
                    and cand.normalized_phone
                    and normalized_phone != cand.normalized_phone
                ):
                    continue
                addr_match = cls.are_addresses_matching(
                    address, cand.address, postal_code, cand.postal_code, city=city or cand.city
                )
                if addr_match is False:
                    continue
                return cand

        # 4. Check business_name + Supporting Metadata
        clean_name = business_name.strip() if business_name else ""
        if not clean_name:
            return None

        clean_city = city.strip() if city else ""
        name_conditions = [
            or_(
                func.lower(Business.canonical_name) == clean_name.lower(),
                func.lower(Business.business_name) == clean_name.lower(),
            )
        ]
        if clean_city:
            name_conditions.append(func.lower(Business.city) == clean_city.lower())

        stmt = select(Business).where(and_(*name_conditions)).limit(20)
        res = await session.execute(stmt)
        candidates = res.scalars().all()

        for cand in candidates:
            if (
                normalized_phone
                and cand.normalized_phone
                and normalized_phone != cand.normalized_phone
            ):
                continue

            if (
                normalized_website
                and cand.normalized_website
                and normalized_website not in GENERIC_DOMAINS
                and cand.normalized_website not in GENERIC_DOMAINS
                and normalized_website != cand.normalized_website
            ):
                continue

            addr_match = cls.are_addresses_matching(
                address, cand.address, postal_code, cand.postal_code, city=clean_city or cand.city
            )
            if addr_match is False:
                continue

            coord_match = None
            if latitude is not None and longitude is not None:
                pass

            if addr_match is True:
                return cand

            if coord_match is True:
                return cand

        return None

    @classmethod
    async def is_duplicate(
        cls,
        session: AsyncSession,
        normalized_phone: str | None,
        normalized_website: str | None,
        business_name: str,
        city: str | None,
        source_platform: str | None = None,
        source_place_id: str | None = None,
        address: str | None = None,
        postal_code: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> bool:
        """Checks if a business already exists based on supporting identifiers."""
        dup = await cls.find_duplicate(
            session,
            normalized_phone=normalized_phone,
            normalized_website=normalized_website,
            business_name=business_name,
            city=city,
            source_platform=source_platform,
            source_place_id=source_place_id,
            address=address,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
        )
        return dup is not None


# Convenience functional aliases
normalize_phone = LeadDeduplicator.normalize_phone
normalize_website = LeadDeduplicator.normalize_website
is_duplicate = LeadDeduplicator.is_duplicate
find_duplicate = LeadDeduplicator.find_duplicate
normalize_address = LeadDeduplicator.normalize_address
are_addresses_matching = LeadDeduplicator.are_addresses_matching
are_coordinates_matching = LeadDeduplicator.are_coordinates_matching
