"""
FastUI Brand Intelligence Extractor
===================================
Extracts authentic clinic branding, logo hierarchy, favicons,
and metadata from official website HTML and structured data.
"""

import json
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from contracts import EnrichedBrand

logger = logging.getLogger("fastui.worker.enrichment.brand")


def extract_brand_intelligence(soup: BeautifulSoup, base_url: str) -> EnrichedBrand:
    """
    Extracts brand assets following the priority order:
    1. JSON-LD Organization/Dentist.logo
    2. Apple Touch Icon
    3. High-resolution Favicon
    4. Header/Navbar Logo Image
    5. OpenGraph Image Fallback
    """
    brand = EnrichedBrand()

    # 1. Meta Title & Description
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        brand.meta_title = title_tag.string.strip()

    meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if meta_desc and meta_desc.get("content"):
        brand.meta_description = meta_desc["content"].strip()

    # Theme Color
    theme_color = soup.find("meta", attrs={"name": re.compile(r"^theme-color$", re.I)})
    if theme_color and theme_color.get("content"):
        brand.theme_color = theme_color["content"].strip()

    # OpenGraph Tags
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        brand.og_title = og_title["content"].strip()

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        brand.og_description = og_desc["content"].strip()

    og_img = soup.find("meta", attrs={"property": "og:image"})
    if og_img and og_img.get("content"):
        brand.og_image_url = urljoin(base_url, og_img["content"].strip())

    og_site_name = soup.find("meta", attrs={"property": "og:site_name"})
    if og_site_name and og_site_name.get("content"):
        brand.brand_name = og_site_name["content"].strip()

    # Favicon resolution
    fav_link = (
        soup.find("link", attrs={"rel": lambda r: r and "apple-touch-icon" in r.lower()})
        or soup.find(
            "link", attrs={"rel": lambda r: r and "icon" in r.lower() and "svg" in str(r).lower()}
        )
        or soup.find("link", attrs={"rel": lambda r: r and "icon" in r.lower()})
        or soup.find("link", attrs={"rel": lambda r: r and "shortcut icon" in r.lower()})
    )
    if fav_link and fav_link.get("href"):
        brand.favicon_url = urljoin(base_url, fav_link["href"].strip())

    # ─────────────────────────────────────────────────────────────
    # Logo Resolution Hierarchy
    # ─────────────────────────────────────────────────────────────

    # 1. JSON-LD Structured Data
    json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in json_ld_scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Handle @graph wrapper
                graph_items = item.get("@graph", [item])
                for g_item in graph_items:
                    if not isinstance(g_item, dict):
                        continue
                    item_type = str(g_item.get("@type", "")).lower()
                    if any(
                        t in item_type
                        for t in ("dentist", "localbusiness", "organization", "medicalbusiness")
                    ):
                        # Logo field
                        logo_field = g_item.get("logo") or g_item.get("image")
                        if logo_field:
                            logo_raw = None
                            if isinstance(logo_field, str):
                                logo_raw = logo_field
                            elif isinstance(logo_field, dict):
                                logo_raw = logo_field.get("url") or logo_field.get("contentUrl")

                            if logo_raw:
                                brand.logo_url = urljoin(base_url, logo_raw.strip())
                                brand.logo_source = "json_ld"
                                brand.logo_confidence = 0.95
                                brand.logo_type = _detect_image_type(brand.logo_url)
                                if not brand.brand_name and g_item.get("name"):
                                    brand.brand_name = g_item["name"].strip()
                                break
                if brand.logo_url:
                    break
        except Exception:
            pass

    # 2. Apple Touch Icon (clean square brand asset)
    if not brand.logo_url:
        apple_icon = soup.find(
            "link", attrs={"rel": lambda r: r and "apple-touch-icon" in r.lower()}
        )
        if apple_icon and apple_icon.get("href"):
            brand.logo_url = urljoin(base_url, apple_icon["href"].strip())
            brand.logo_source = "apple_touch_icon"
            brand.logo_confidence = 0.85
            brand.logo_type = _detect_image_type(brand.logo_url)

    # 3. High-resolution Favicon (SVG or large PNG)
    if not brand.logo_url:
        high_res_fav = soup.find(
            "link",
            attrs={
                "rel": lambda r: r and "icon" in r.lower(),
                "sizes": lambda s: (
                    s and any(dim in s for dim in ("192x192", "512x512", "180x180", "128x128"))
                ),
            },
        ) or soup.find(
            "link",
            attrs={
                "rel": lambda r: r and "icon" in r.lower(),
                "type": lambda t: t and "svg" in t.lower(),
            },
        )
        if high_res_fav and high_res_fav.get("href"):
            brand.logo_url = urljoin(base_url, high_res_fav["href"].strip())
            brand.logo_source = "favicon"
            brand.logo_confidence = 0.75
            brand.logo_type = _detect_image_type(brand.logo_url)

    # 4. Header / Navbar Logo Image
    if not brand.logo_url:
        header_el = soup.find(["header", "nav"]) or soup
        logo_img = (
            header_el.find("img", attrs={"class": re.compile(r"logo", re.I)})
            or header_el.find("img", attrs={"id": re.compile(r"logo", re.I)})
            or header_el.find("img", attrs={"alt": re.compile(r"logo|brand", re.I)})
            or header_el.find("a", attrs={"class": re.compile(r"brand|logo", re.I)}, recursive=True)
        )
        if logo_img:
            if logo_img.name == "a":
                sub_img = logo_img.find("img")
                if sub_img and sub_img.get("src"):
                    logo_img = sub_img

            src = logo_img.get("src") or logo_img.get("data-src")
            if src and not src.startswith("data:"):
                brand.logo_url = urljoin(base_url, src.strip())
                brand.logo_source = "header_img"
                brand.logo_confidence = 0.70
                brand.logo_type = _detect_image_type(brand.logo_url)

    # 5. OpenGraph Image Fallback
    if not brand.logo_url and brand.og_image_url:
        # Only use OG image if it is not an obvious full hero photo
        brand.logo_url = brand.og_image_url
        brand.logo_source = "og_image"
        brand.logo_confidence = 0.50
        brand.logo_type = _detect_image_type(brand.logo_url)

    return brand


def _detect_image_type(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    clean = url.lower().split("?")[0].split("#")[0]
    for ext in ("svg", "png", "webp", "jpg", "jpeg", "ico"):
        if clean.endswith(f".{ext}"):
            return ext
    return "png"
