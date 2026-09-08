"""
FastUI Website Quality Analyzer
===============================
Evaluates public clinic websites across technical, conversion,
mobile, and SEO readiness metrics, computing an objective quality score (0-100).
"""

from typing import Dict, Any
from bs4 import BeautifulSoup

from contracts import EnrichedQualityAudit, EnrichedBrand, EnrichedContact


def evaluate_website_quality(
    soup: BeautifulSoup,
    url: str,
    brand: EnrichedBrand,
    contact: EnrichedContact
) -> EnrichedQualityAudit:
    """
    Computes objective website quality score and component breakdown.
    """
    has_ssl = url.lower().startswith("https://")
    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    has_mobile_viewport = bool(viewport_tag and "width=device-width" in viewport_tag.get("content", "").lower())
    has_meta_description = bool(brand.meta_description and len(brand.meta_description) >= 40)
    has_structured_data = bool(soup.find("script", attrs={"type": "application/ld+json"}))
    has_social_presence = bool(contact.social_links)
    has_online_booking = bool(contact.booking_urls)
    has_whatsapp_cta = bool(contact.whatsapp)
    has_clear_contact = bool(contact.phones or contact.emails)
    has_logo = bool(brand.logo_url)

    # Calculate weighted score (0 to 100)
    score = 0
    breakdown: Dict[str, Any] = {}

    # Security & Foundation (25 pts)
    ssl_pts = 15 if has_ssl else 0
    mobile_pts = 10 if has_mobile_viewport else 0
    score += ssl_pts + mobile_pts
    breakdown["security_and_mobile"] = {"ssl": ssl_pts, "mobile_viewport": mobile_pts}

    # SEO & Brand Identity (25 pts)
    logo_pts = 10 if has_logo else 0
    desc_pts = 5 if has_meta_description else 0
    schema_pts = 10 if has_structured_data else 0
    score += logo_pts + desc_pts + schema_pts
    breakdown["branding_and_seo"] = {"logo": logo_pts, "meta_description": desc_pts, "schema_markup": schema_pts}

    # Conversion & Direct Contact (35 pts)
    contact_pts = 15 if has_clear_contact else 0
    booking_pts = 10 if has_online_booking else 0
    whatsapp_pts = 10 if has_whatsapp_cta else 0
    score += contact_pts + booking_pts + whatsapp_pts
    breakdown["conversion_readiness"] = {"contact_info": contact_pts, "online_booking": booking_pts, "whatsapp_cta": whatsapp_pts}

    # Digital Footprint (15 pts)
    social_pts = 15 if has_social_presence else 0
    score += social_pts
    breakdown["social_presence"] = {"social_profiles": social_pts}

    return EnrichedQualityAudit(
        score=min(100, score),
        has_ssl=has_ssl,
        has_mobile_viewport=has_mobile_viewport,
        has_meta_description=has_meta_description,
        has_structured_data=has_structured_data,
        has_social_presence=has_social_presence,
        has_online_booking=has_online_booking,
        has_whatsapp_cta=has_whatsapp_cta,
        has_clear_contact=has_clear_contact,
        breakdown=breakdown,
    )
