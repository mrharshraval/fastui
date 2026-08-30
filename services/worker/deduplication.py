"""
FastUI Worker Deduplication
============================
In-memory deduplication helpers for merging leads from multiple sources
before returning them to the API. No database access — that is the API's job.
"""

import re
from typing import Optional
from urllib.parse import urlparse


class LeadDeduplicator:
    """
    In-memory phone and website normalization for cross-source deduplication.
    """

    @staticmethod
    def normalize_phone(phone: Optional[str]) -> Optional[str]:
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
