"""
FastUI Lead Deduplication Service
=================================
High-precision entity resolution and normalization rules for discovered business records.
"""

import re
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy import and_, func, or_, select
from models.schema import Business, BusinessSource


from utils.phone import normalize_global_phone, resolve_country_code


class LeadDeduplicator:
    """
    Encapsulates phone, website, place ID, and business entity deduplication algorithms.
    """

    @staticmethod
    def format_display_phone(phone: Optional[str], location: Optional[str] = None) -> Optional[str]:
        """
        Formats phone number for clean human display with universal country code.
        Strips domestic trunk '0' and standardizes worldwide.
        """
        display_phone, _ = normalize_global_phone(phone, location=location)
        return display_phone

    @staticmethod
    def normalize_phone(phone: Optional[str], location: Optional[str] = None) -> Optional[str]:
        """
        Normalizes a phone number to canonical E.164-style standard format (+<digits>).
        Strips whitespace, hyphens, parentheses, and leading trunk zeros.
        """
        _, e164 = normalize_global_phone(phone, location=location)
        return e164

    @staticmethod
    def normalize_website(website: Optional[str]) -> Optional[str]:
        """
        Normalizes a website URL to its canonical base hostname.
        Strips protocols, www subdomains, port numbers, paths, query strings, and fragments.
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
    async def find_duplicate(
        session,
        normalized_phone: Optional[str],
        normalized_website: Optional[str],
        business_name: str,
        city: Optional[str],
        source_platform: Optional[str] = None,
        source_place_id: Optional[str] = None,
    ) -> Optional[Business]:
        """
        Finds existing Business entity based on deduplication hierarchy:
        1. Exact match on source platform + external_id in BusinessSource
        2. Exact match on normalized_website
        3. Exact match on normalized_phone
        4. Exact match on business_name + city (case-insensitive)
        """
        # 1. Check BusinessSource external_id (strongest ID)
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

        # 2. Check website / phone / name+city
        conditions = []
        if normalized_website:
            conditions.append(Business.normalized_website == normalized_website)
        if normalized_phone:
            conditions.append(Business.normalized_phone == normalized_phone)

        clean_name = business_name.strip() if business_name else ""
        clean_city = city.strip() if city else ""

        if clean_name and clean_city:
            conditions.append(
                and_(
                    func.lower(Business.business_name) == clean_name.lower(),
                    func.lower(Business.city) == clean_city.lower(),
                )
            )
        elif clean_name and not normalized_website and not normalized_phone:
            conditions.append(func.lower(Business.business_name) == clean_name.lower())

        if not conditions:
            return None

        query = select(Business).where(or_(*conditions)).limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def is_duplicate(
        session,
        normalized_phone: Optional[str],
        normalized_website: Optional[str],
        business_name: str,
        city: Optional[str],
        source_platform: Optional[str] = None,
        source_place_id: Optional[str] = None,
    ) -> bool:
        """
        Checks if a business already exists based on deduplication signals.
        """
        dup = await LeadDeduplicator.find_duplicate(
            session,
            normalized_phone=normalized_phone,
            normalized_website=normalized_website,
            business_name=business_name,
            city=city,
            source_platform=source_platform,
            source_place_id=source_place_id,
        )
        return dup is not None


# Module-level convenience functions
normalize_phone = LeadDeduplicator.normalize_phone
normalize_website = LeadDeduplicator.normalize_website
is_duplicate = LeadDeduplicator.is_duplicate
find_duplicate = LeadDeduplicator.find_duplicate

