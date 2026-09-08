"""
FastUI Contact & Conversion Intelligence Extractor
==================================================
Extracts public contact points, WhatsApp links, booking URLs,
and appointment provider CTAs from website HTML.
"""

import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from contracts import EnrichedContact
from utils.phone import normalize_global_phone, is_mobile_phone, get_whatsapp_url

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

BOOKING_DOMAINS = {
    "practo.com": "Practo",
    "zocdoc.com": "Zocdoc",
    "doctolib": "Doctolib",
    "calendly.com": "Calendly",
    "setmore.com": "Setmore",
    "acuityscheduling.com": "Acuity",
}


def extract_contact_conversion(soup: BeautifulSoup, base_url: str, location_hint: str = "") -> EnrichedContact:
    """
    Extracts emails, phones, WhatsApp links, and booking platform URLs.
    """
    contact = EnrichedContact()
    seen_emails = set()
    seen_phones = set()

    # 1. Emails from mailto links & body regex
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            email_val = href[7:].split("?")[0].strip().lower()
            if _is_valid_email(email_val) and email_val not in seen_emails:
                seen_emails.add(email_val)
                contact.emails.append(email_val)

    # Fallback to regex in body
    text_content = soup.get_text(separator=" ")
    for email_match in EMAIL_REGEX.findall(text_content):
        e_clean = email_match.strip().lower()
        if _is_valid_email(e_clean) and e_clean not in seen_emails:
            seen_emails.add(e_clean)
            contact.emails.append(e_clean)

    # 2. Phones from tel: links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("tel:"):
            raw_p = href[4:].split("?")[0].strip()
            display_p, _ = normalize_global_phone(raw_p, location=location_hint)
            if display_p and display_p not in seen_phones:
                seen_phones.add(display_p)
                contact.phones.append(display_p)

    # 3. WhatsApp links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if any(w in href.lower() for w in ("wa.me/", "api.whatsapp.com/send", "whatsapp://", "whatsapp.com")):
            digits = re.sub(r"\D", "", href)
            if len(digits) >= 10:
                contact.whatsapp = f"+{digits}"
                contact.whatsapp_url = f"https://wa.me/{digits}"
                break

    # If no explicit link in HTML, check if any phone is a mobile line
    if not contact.whatsapp:
        for p in contact.phones:
            if is_mobile_phone(p, location=location_hint):
                contact.whatsapp = p
                contact.whatsapp_url = get_whatsapp_url(p, location=location_hint)
                break

    # 4. Booking Platforms & Links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        href_lower = href.lower()

        # Check known third-party booking providers
        for domain, provider_name in BOOKING_DOMAINS.items():
            if domain in href_lower:
                if href not in contact.booking_urls:
                    contact.booking_urls.append(href)
                    contact.booking_provider = provider_name
                break

        # Check internal booking URLs
        if any(path in href_lower for path in ("/book", "/appointment", "/schedule", "/online-booking")):
            full_url = urljoin(base_url, href)
            if full_url not in contact.booking_urls:
                contact.booking_urls.append(full_url)
                if not contact.booking_provider:
                    contact.booking_provider = "Clinic Direct"

        # Check contact page link
        if any(path in href_lower for path in ("/contact", "/contact-us", "/reach-us", "/locate-us")):
            if not contact.contact_page_url:
                contact.contact_page_url = urljoin(base_url, href)

    return contact


def _is_valid_email(email: str) -> bool:
    if not email or len(email) < 6:
        return False
    # Filter out code artifacts and dummy examples
    for ignore in ("example.com", "domain.com", "sentry.io", "wix.com", "schema.org", ".png", ".jpg"):
        if ignore in email:
            return False
    return True
