"""
Unit tests for the Website Enrichment subsystem.
Tests SSRF protection, logo hierarchy, dental specialties, doctor credentials,
booking conversion signals, and website quality evaluation using static fixtures.
"""

from pathlib import Path
from bs4 import BeautifulSoup
import pytest

from enrichment.client import validate_target_url
from enrichment.brand import extract_brand_intelligence
from enrichment.dental import analyze_dental_treatments
from enrichment.practitioner import extract_practitioners
from enrichment.conversion import extract_contact_conversion
from enrichment.technology import detect_website_technology
from enrichment.social import extract_social_links
from enrichment.hours import extract_opening_hours
from enrichment.quality import evaluate_website_quality

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_ssrf_url_validation():
    # Dangerous URLs must be rejected
    unsafe_urls = [
        "http://localhost:8000/admin",
        "http://127.0.0.1/private",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
        "ftp://example.com/file",
        "",
        None,
    ]
    for url in unsafe_urls:
        is_safe, msg = validate_target_url(url)
        assert is_safe is False, f"URL '{url}' should have been blocked for SSRF!"

    # Safe public URLs must be accepted
    safe_urls = [
        "https://www.google.com",
        "https://smiledentalstudio.example.com/about",
        "http://www.colgate.com",
    ]
    for url in safe_urls:
        is_safe, _ = validate_target_url(url)
        # In isolated CI or test environments, public DNS might not resolve or might succeed
        # Just check it doesn't crash


def test_brand_intelligence_with_fixture():
    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://smiledentalstudio.example.com"

    brand = extract_brand_intelligence(soup, base_url)

    # 1. Logo extracted from JSON-LD (highest priority)
    assert brand.logo_url == "https://smiledentalstudio.example.com/assets/brand-logo.png"
    assert brand.logo_source == "json_ld"
    assert brand.logo_confidence >= 0.90
    assert brand.logo_type == "png"

    # 2. Favicon extracted
    assert brand.favicon_url == "https://smiledentalstudio.example.com/assets/apple-touch-icon.png"

    # 3. Meta title & theme color
    assert "Smile Dental Studio" in (brand.meta_title or "")
    assert brand.theme_color == "#0d9488"
    assert "Award-winning dental clinic" in (brand.meta_description or "")


def test_dental_specialties_analyzer():
    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    treatments = analyze_dental_treatments(soup)

    # Required detected specialties
    assert treatments["Dental Implants"].detected is True
    assert treatments["Dental Implants"].confidence >= 0.70
    assert "all-on-4" in treatments["Dental Implants"].keywords_matched or "dental implant" in treatments["Dental Implants"].keywords_matched

    assert treatments["Invisalign"].detected is True
    assert treatments["Cosmetic Dentistry"].detected is True
    assert treatments["Root Canal"].detected is True
    assert treatments["Pediatric Dentistry"].detected is True
    assert treatments["Oral Surgery"].detected is True
    assert treatments["Emergency Dentistry"].detected is True
    assert treatments["Periodontics"].detected is True
    assert treatments["Sedation Dentistry"].detected is True


def test_doctor_practitioner_extractor():
    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    doctors, primary_doctor = extract_practitioners(soup)

    assert len(doctors) >= 1
    assert primary_doctor is not None
    assert "Anil Sharma" in primary_doctor.name
    assert "Chief" in (primary_doctor.title or "")
    assert primary_doctor.is_primary is True
    assert primary_doctor.confidence >= 0.85


def test_contact_conversion_extractor():
    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://smiledentalstudio.example.com"

    contact = extract_contact_conversion(soup, base_url)

    assert "info@smiledentalstudio.com" in contact.emails
    assert contact.whatsapp == "+919876543210"
    assert contact.booking_provider == "Practo"
    assert any("practo.com" in url for url in contact.booking_urls)


def test_technology_and_social_extractors():
    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    tech = detect_website_technology(soup, html)
    assert tech.cms == "WordPress"

    social = extract_social_links(soup)
    assert "instagram" in social
    assert "facebook" in social
    assert "linkedin" in social
    assert "youtube" in social


def test_website_quality_audit():
    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://smiledentalstudio.example.com"

    brand = extract_brand_intelligence(soup, base_url)
    contact = extract_contact_conversion(soup, base_url)
    contact.social_links = extract_social_links(soup)

    quality = evaluate_website_quality(soup, base_url, brand, contact)

    assert quality.score >= 80
    assert quality.has_ssl is True
    assert quality.has_mobile_viewport is True
    assert quality.has_structured_data is True
    assert quality.has_online_booking is True
    assert quality.has_whatsapp_cta is True
    assert quality.has_social_presence is True


def test_enriched_brand_name_property():
    from contracts import EnrichedBrand
    brand = EnrichedBrand(brand_name="Suman Dental Care", logo_url="https://example.com/logo.png")
    assert brand.brand_name == "Suman Dental Care"
    assert brand.name == "Suman Dental Care"


@pytest.mark.asyncio
async def test_orchestrator_enrich_website_flow():
    from unittest.mock import AsyncMock
    from enrichment.orchestrator import WebsiteEnrichmentEngine
    from contracts import EnrichmentParams

    fixture_path = FIXTURES_DIR / "dental_clinic_website.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()

    orchestrator = WebsiteEnrichmentEngine()
    orchestrator.client.fetch_html = AsyncMock(return_value=(html, "https://smiledentalstudio.example.com", None))

    params = EnrichmentParams(
        website="https://smiledentalstudio.example.com",
        business_name="Smile Dental Studio",
        max_pages=2,
    )
    result = await orchestrator.enrich_website(params)

    assert result.success is True
    assert result.profile is not None
    assert result.profile.brand.logo_url == "https://smiledentalstudio.example.com/assets/brand-logo.png"
    assert result.profile.brand.brand_name == "Smile Dental Studio"
    assert result.profile.brand.name == "Smile Dental Studio"
    assert len(result.profile.treatments) > 0


def test_social_media_and_youtube_extraction():
    sample_html = """
    <html>
        <body>
            <a href="https://www.instagram.com/smiledentalcare">Instagram</a>
            <a href="https://facebook.com/smiledentalcare">Facebook</a>
            <a href="https://youtube.com/@smiledentalcare">YouTube Channel</a>
            <a href="https://twitter.com/smiledental">Twitter</a>
            <a href="https://wa.me/919876543210">Chat on WhatsApp</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(sample_html, "html.parser")
    social = extract_social_links(soup)
    assert social.get("instagram") == "https://instagram.com/smiledentalcare"
    assert social.get("facebook") == "https://facebook.com/smiledentalcare"
    assert social.get("youtube") == "https://youtube.com/@smiledentalcare"
    assert social.get("twitter") == "https://twitter.com/smiledental"

    contact = extract_contact_conversion(soup, "https://smiledental.com")
    assert contact.whatsapp == "+919876543210"
    assert contact.whatsapp_url == "https://wa.me/919876543210"

