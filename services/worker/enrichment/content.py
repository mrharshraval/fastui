"""
FastUI Comprehensive Content & Semantic Intelligence Extractor
==============================================================
Extracts authentic clinic content across all relevant pages:
- Tagline & About / Mission Statements
- Testimonials & Patient Reviews (HTML + JSON-LD)
- FAQs (Questions & Answers)
- Clinical Facilities & Technologies
- Certifications & Accreditations
- Insurance, Payment, & Financing Options
- Emergency Dental Services
- Unique Selling Points (USPs)
- Multi-Branch / Location Profiles
- Reusable Website Images (Hero, Clinic, Team, Gallery)
- Brand Colors & Palette Signals
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from contracts import (
    EnrichedBranch,
    EnrichedFAQ,
    EnrichedTestimonial,
)

logger = logging.getLogger("fastui.worker.enrichment.content")

# Reusable image file extension pattern
IMAGE_EXT_REGEX = re.compile(r"\.(?:png|jpe?g|webp|avif)(?:\?.*)?$", re.I)

# Common clinical amenities & technologies taxonomy
FACILITY_KEYWORDS = {
    "CBCT 3D Imaging": ["cbct", "3d imaging", "cone beam", "3d scan"],
    "Digital X-Rays": ["digital x-ray", "digital radiograph", "rvg", "intraoral x-ray"],
    "Intraoral Scanner": ["intraoral scanner", "3d intraoral", "digital impression", "trios", "itero"],
    "Laser Dentistry": ["laser dentistry", "dental laser", "diode laser", "biolase", "waterlase"],
    "CAD/CAM Digital Lab": ["cad/cam", "cerec", "same day crown", "digital smile design", "dsd"],
    "Sterilization Protocol": ["autoclave", "sterilization room", "class b autoclave", "infection control", "100% sterile"],
    "Painless Anesthesia": ["computerized anesthesia", "painless injection", "the wand", "needle-free"],
    "Wheelchair Accessible": ["wheelchair accessible", "handicap accessible", "ramp access"],
    "On-Site Parking": ["free parking", "valet parking", "parking available", "dedicated parking"],
    "Wi-Fi & Lounge": ["wi-fi", "wifi", "comfort lounge", "beverage bar", "tv in operatory"],
}

# Certifications & Accreditations
CERTIFICATION_KEYWORDS = {
    "ISO Certified": [r"\biso\s*\d{4,5}\b", r"iso\s*certified"],
    "NABH Accredited": [r"\bnabh\b", r"national accreditation board"],
    "IDA Member": [r"\bida\b", r"indian dental association"],
    "ADA Member": [r"\bada\b", r"american dental association"],
    "Invisalign Diamond Provider": [r"invisalign\s*diamond", r"invisalign\s*platinum", r"invisalign\s*provider"],
    "Nobel Biocare Certified": [r"nobel\s*biocare", r"straumann\s*certified"],
    "ICOI Fellow": [r"\bicoi\b", r"international congress of oral implantologists"],
}

# Insurance Providers
INSURANCE_KEYWORDS = [
    "Delta Dental", "Cigna", "Aetna", "MetLife", "Guardian", "United Healthcare",
    "Blue Cross Blue Shield", "Humana", "Star Health", "Max Bupa", "HDFC ERGO",
    "Bajaj Allianz", "Care Health", "ICICI Lombard", "Niva Bupa", "Reliance Health"
]


def extract_tagline(soup: BeautifulSoup, brand_name: Optional[str] = None) -> Optional[str]:
    """
    Extracts authentic clinic tagline or slogan from hero headings or meta descriptions.
    """
    # 1. Look for explicit tagline classes or attributes
    tagline_elem = soup.find(class_=re.compile(r"tagline|slogan|hero-sub|sub-heading|banner-sub", re.I))
    if tagline_elem:
        text = tagline_elem.get_text(separator=" ", strip=True)
        if 10 <= len(text) <= 140:
            return text

    # 2. Look for primary hero h1/h2 that functions as a tagline
    for h in soup.find_all(["h1", "h2"])[:4]:
        text = h.get_text(separator=" ", strip=True)
        # Avoid generic single-word headings or exact brand name repetition
        if brand_name and text.lower() == brand_name.lower():
            continue
        if 15 <= len(text) <= 120 and any(w in text.lower() for w in ("smile", "care", "dental", "gentle", "health", "specialist", "trusted")):
            return text

    return None


def extract_about_and_mission(soup: BeautifulSoup) -> Optional[str]:
    """
    Extracts clinic about description or mission statement from About sections or paragraphs.
    """
    about_containers = soup.find_all(
        ["section", "div", "article"],
        attrs={"id": re.compile(r"about|mission|story|philosophy", re.I)}
    ) or soup.find_all(
        ["section", "div", "article"],
        attrs={"class": re.compile(r"about|mission|story|philosophy|overview", re.I)}
    )

    for container in about_containers[:3]:
        paragraphs = container.find_all("p")
        for p in paragraphs:
            text = p.get_text(separator=" ", strip=True)
            if 60 <= len(text) <= 500:
                # Discard copyright/footer text
                if any(w in text.lower() for w in ("copyright", "all rights reserved", "terms of service", "privacy policy")):
                    continue
                return text

    # Fallback to meta description
    meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"].strip()
        if 40 <= len(desc) <= 300:
            return desc

    return None


def extract_testimonials(soup: BeautifulSoup) -> List[EnrichedTestimonial]:
    """
    Extracts patient testimonials and reviews from JSON-LD structured data and HTML review cards.
    """
    testimonials: List[EnrichedTestimonial] = []
    seen_texts = set()

    # 1. JSON-LD Reviews
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                graph = item.get("@graph", [item])
                for entity in graph:
                    if not isinstance(entity, dict):
                        continue
                    # Handle Review items
                    reviews = entity.get("review") or entity.get("reviews")
                    if isinstance(reviews, dict):
                        reviews = [reviews]
                    elif not isinstance(reviews, list):
                        reviews = [entity] if entity.get("@type") == "Review" else []

                    for r in reviews:
                        if not isinstance(r, dict):
                            continue
                        author_obj = r.get("author") or {}
                        author_name = author_obj.get("name") if isinstance(author_obj, dict) else str(author_obj)
                        body = r.get("reviewBody") or r.get("description") or ""
                        if body and len(body.strip()) > 20:
                            clean_text = body.strip()
                            sig = clean_text[:50].lower()
                            if sig not in seen_texts:
                                seen_texts.add(sig)
                                rating_val = 5.0
                                rating_obj = r.get("reviewRating") or {}
                                if isinstance(rating_obj, dict) and rating_obj.get("ratingValue"):
                                    try:
                                        rating_val = float(rating_obj["ratingValue"])
                                    except (ValueError, TypeError):
                                        pass
                                testimonials.append(EnrichedTestimonial(
                                    name=author_name.strip() if author_name else "Verified Patient",
                                    quote=clean_text[:400],
                                    rating=rating_val,
                                    date=r.get("datePublished")
                                ))
        except Exception:
            pass

    # 2. HTML Testimonial Cards
    if len(testimonials) < 6:
        review_cards = soup.find_all(
            ["div", "article", "blockquote"],
            attrs={"class": re.compile(r"testimonial|review|patient-quote|feedback|client-card", re.I)}
        )
        for card in review_cards:
            text_elem = card.find(["p", "blockquote", "q", "span"])
            if not text_elem:
                continue
            quote = text_elem.get_text(separator=" ", strip=True)
            if 30 <= len(quote) <= 450:
                sig = quote[:50].lower()
                if sig not in seen_texts:
                    seen_texts.add(sig)
                    author_elem = card.find(class_=re.compile(r"name|author|patient|client|user", re.I))
                    author_name = author_elem.get_text(strip=True) if author_elem else "Verified Patient"
                    # Clean up common title artifacts
                    author_name = re.sub(r"^(by|patient|verified|review by)\s*", "", author_name, flags=re.I).strip()
                    if not author_name or len(author_name) > 40:
                        author_name = "Verified Patient"
                    testimonials.append(EnrichedTestimonial(
                        name=author_name,
                        quote=quote,
                        rating=5.0
                    ))
            if len(testimonials) >= 6:
                break

    return testimonials[:6]


def extract_faqs(soup: BeautifulSoup) -> List[EnrichedFAQ]:
    """
    Extracts FAQs from JSON-LD FAQPage schema and HTML accordion blocks.
    """
    faqs: List[EnrichedFAQ] = []
    seen_q = set()

    # 1. JSON-LD FAQPage
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                graph = item.get("@graph", [item])
                for entity in graph:
                    if not isinstance(entity, dict):
                        continue
                    if entity.get("@type") == "FAQPage" or "mainEntity" in entity:
                        main_entity = entity.get("mainEntity", [])
                        if isinstance(main_entity, dict):
                            main_entity = [main_entity]
                        for q_item in main_entity:
                            if not isinstance(q_item, dict):
                                continue
                            q_text = q_item.get("name", "").strip()
                            ans_obj = q_item.get("acceptedAnswer", {})
                            ans_text = ans_obj.get("text", "").strip() if isinstance(ans_obj, dict) else ""
                            if q_text and ans_text and q_text.lower() not in seen_q:
                                seen_q.add(q_text.lower())
                                # Strip HTML tags from answer text
                                clean_ans = re.sub(r"<[^>]+>", " ", ans_text)
                                clean_ans = " ".join(clean_ans.split())
                                faqs.append(EnrichedFAQ(
                                    question=q_text,
                                    answer=clean_ans[:500]
                                ))
        except Exception:
            pass

    # 2. HTML Accordion / FAQ blocks
    if len(faqs) < 8:
        faq_containers = soup.find_all(
            ["div", "section", "dl"],
            attrs={"class": re.compile(r"faq|accordion|question", re.I)}
        )
        for container in faq_containers:
            # Check <details> <summary>
            for details in container.find_all("details"):
                summary = details.find("summary")
                if summary:
                    q = summary.get_text(strip=True)
                    # Clone details without summary to get answer text
                    ans = " ".join([elem.get_text(strip=True) for elem in details.children if elem != summary and elem.name])
                    if q and ans and q.lower() not in seen_q and 10 <= len(q) <= 150:
                        seen_q.add(q.lower())
                        faqs.append(EnrichedFAQ(question=q, answer=ans[:400]))

            # Check heading + paragraph patterns
            headings = container.find_all(["h3", "h4", "strong", "dt"])
            for h in headings:
                q = h.get_text(strip=True)
                if "?" in q and 10 <= len(q) <= 150 and q.lower() not in seen_q:
                    # Find sibling paragraph or next element
                    sibling = h.find_next_sibling(["p", "div", "dd"])
                    if sibling:
                        ans = sibling.get_text(strip=True)
                        if ans and len(ans) > 20:
                            seen_q.add(q.lower())
                            faqs.append(EnrichedFAQ(question=q, answer=ans[:400]))
                if len(faqs) >= 8:
                    break

    return faqs[:8]


def extract_facilities_and_amenities(soup: BeautifulSoup) -> List[str]:
    """
    Scans website content for clinical technologies, equipment, and patient amenities.
    """
    text = soup.get_text(separator=" ", strip=True).lower()
    detected = []

    for name, keywords in FACILITY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            detected.append(name)

    return detected


def extract_certifications(soup: BeautifulSoup) -> List[str]:
    """
    Scans for dental and clinical certifications, associations, and accreditations.
    """
    text = soup.get_text(separator=" ", strip=True)
    detected = []

    for name, patterns in CERTIFICATION_KEYWORDS.items():
        if any(re.search(pat, text, re.I) for pat in patterns):
            detected.append(name)

    return detected


def extract_insurance_info(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extracts insurance providers and financing options mentioned on website.
    """
    text = soup.get_text(separator=" ", strip=True)
    text_lower = text.lower()

    providers = []
    for provider in INSURANCE_KEYWORDS:
        if re.search(r"\b" + re.escape(provider.lower()) + r"\b", text_lower):
            providers.append(provider)

    has_emi = bool(re.search(r"\b(no\s*cost\s*emi|0%\s*emi|flexible\s*emi|installment|financing)\b", text_lower))
    has_membership = bool(re.search(r"\b(membership\s*plan|dental\s*plan|annual\s*plan|discount\s*plan)\b", text_lower))

    return {
        "providers": providers,
        "has_emi": has_emi,
        "has_membership": has_membership,
    }


def extract_emergency_services(soup: BeautifulSoup) -> Optional[str]:
    """
    Extracts emergency dental care notes or 24/7 availability signals.
    """
    text = soup.get_text(separator=" ", strip=True)
    match = re.search(
        r"(?:24[/-]7|same[ -]day|immediate)\s+(?:emergency|urgent|toothache)\s+(?:care|dentistry|appointment|relief|service)?",
        text,
        re.I
    )
    if match:
        return match.group(0).capitalize()
    if re.search(r"\bemergency\s+(?:dental|dentist|care|services)\b", text, re.I):
        return "Same-Day Emergency Dental Care Available"
    return None


def extract_unique_selling_points(soup: BeautifulSoup) -> List[str]:
    """
    Extracts quantifiable badges and trust highlights (e.g. '15+ Years Experience', '10k Happy Patients').
    """
    text = soup.get_text(separator=" ", strip=True)
    usps = []

    # Numeric experience / patients patterns
    exp_match = re.search(r"\b(\d{1,2}\+?\s*(?:years|yrs)(?:\s+of)?\s+(?:experience|clinical excellence))\b", text, re.I)
    if exp_match:
        usps.append(exp_match.group(1).title())

    patients_match = re.search(r"\b(\d+[\d,]*\+?\s*(?:happy|satisfied)?\s*(?:patients|smiles|clients))\b", text, re.I)
    if patients_match:
        usps.append(patients_match.group(1).title())

    # Qualitative badges
    if re.search(r"\bpainless\s+(?:dentistry|treatments?|root canal|injections?)\b", text, re.I):
        usps.append("100% Pain-Free Gentle Treatments")

    if re.search(r"\badvanced\s+(?:technology|equipment|digital dentistry)\b", text, re.I):
        usps.append("State-of-the-Art Digital Dental Tech")

    if re.search(r"\btransparent\s+(?:pricing|costs|fees)\b", text, re.I):
        usps.append("Transparent Upfront Pricing")

    return usps[:4]


def extract_branches(soup: BeautifulSoup, base_url: str) -> List[EnrichedBranch]:
    """
    Extracts branch locations or multiple clinic addresses listed on website.
    """
    branches: List[EnrichedBranch] = []
    seen_addresses = set()

    location_sections = soup.find_all(
        ["div", "section", "article"],
        attrs={"class": re.compile(r"branch|location|clinic-address|centre|center", re.I)}
    )

    for sec in location_sections:
        name_elem = sec.find(["h2", "h3", "h4", "strong"])
        branch_name = name_elem.get_text(strip=True) if name_elem else "Clinic Branch"

        p_elem = sec.find("p") or sec
        addr_text = p_elem.get_text(separator=" ", strip=True)
        if 15 <= len(addr_text) <= 200:
            sig = addr_text[:40].lower()
            if sig not in seen_addresses:
                seen_addresses.add(sig)
                # Check for phone in section
                phone_match = re.search(r"(\+?[0-9\s\-()]{10,15})", addr_text)
                branch_phone = phone_match.group(1).strip() if phone_match else None
                branches.append(EnrichedBranch(
                    name=branch_name[:60],
                    address=addr_text[:180],
                    phone=branch_phone
                ))
        if len(branches) >= 8:
            break

    return branches


def extract_reusable_images(soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
    """
    Extracts authentic, high-resolution website images suitable for demo personalization.
    Filters out tracking pixels, icons, advertisement banners, and tiny assets.
    """
    categorized: Dict[str, List[str]] = {
        "hero": [],
        "clinic": [],
        "team": [],
        "gallery": [],
    }
    seen_urls = set()

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            continue
        src = src.strip()
        if src.startswith("data:") or not IMAGE_EXT_REGEX.search(src):
            continue

        full_url = urljoin(base_url, src)
        if full_url in seen_urls:
            continue

        # Filter out tracking pixels and tiny icons
        width = img.get("width")
        height = img.get("height")
        try:
            if width and int(width) < 80:
                continue
            if height and int(height) < 80:
                continue
        except (ValueError, TypeError):
            pass

        # Discard obvious icon / social images
        lower_url = full_url.lower()
        if any(bad in lower_url for bad in ("icon", "logo", "arrow", "star", "social", "badge", "avatar", "flag", "pixel")):
            continue

        seen_urls.add(full_url)
        alt = (img.get("alt") or "").lower()
        parent_class = " ".join(img.parent.get("class", [])) if img.parent else ""
        img_context = f"{lower_url} {alt} {parent_class}".lower()

        if any(k in img_context for k in ("hero", "banner", "slide", "cover")):
            if len(categorized["hero"]) < 3:
                categorized["hero"].append(full_url)
        elif any(k in img_context for k in ("doctor", "dentist", "team", "staff", "portrait")):
            if len(categorized["team"]) < 4:
                categorized["team"].append(full_url)
        elif any(k in img_context for k in ("clinic", "interior", "exterior", "operatory", "office", "facility", "infrastructure")):
            if len(categorized["clinic"]) < 4:
                categorized["clinic"].append(full_url)
        elif any(k in img_context for k in ("before", "after", "result", "smile", "transformation", "case")):
            if len(categorized["gallery"]) < 6:
                categorized["gallery"].append(full_url)

    return categorized


def extract_brand_colors(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extracts brand palette signals from CSS variables, meta theme-color, or prominent styles.
    """
    colors: Dict[str, str] = {}

    # 1. Meta theme-color
    theme_color = soup.find("meta", attrs={"name": re.compile(r"^theme-color$", re.I)})
    if theme_color and theme_color.get("content"):
        val = theme_color["content"].strip()
        if re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", val):
            colors["theme"] = val
            colors["primary"] = val

    # 2. Check inline styles on header or root
    for tag in soup.find_all(["header", "nav", "style", "body"])[:5]:
        style = tag.get("style", "") or (tag.string if tag.name == "style" else "")
        if style:
            # Look for hex codes
            hexes = re.findall(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", style)
            for h in hexes:
                h_lower = h.lower()
                # Skip pure black and pure white
                if h_lower not in ("#000", "#000000", "#fff", "#ffffff"):
                    if "primary" not in colors:
                        colors["primary"] = h_lower
                    elif "secondary" not in colors and h_lower != colors["primary"]:
                        colors["secondary"] = h_lower
                        break

    return colors
