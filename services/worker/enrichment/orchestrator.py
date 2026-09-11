"""
FastUI Website Enrichment Orchestrator
======================================
Coordinates lightweight HTTP retrieval, high-value page discovery,
and multi-module semantic analysis into a feature-rich prospect profile.
"""

import logging
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from contracts import (
    EnrichedBusinessProfile,
    EnrichmentParams,
    EnrichmentResponse,
)
from enrichment.brand import extract_brand_intelligence
from enrichment.client import EnrichmentHttpClient
from enrichment.content import (
    extract_about_and_mission,
    extract_branches,
    extract_brand_colors,
    extract_certifications,
    extract_emergency_services,
    extract_facilities_and_amenities,
    extract_faqs,
    extract_insurance_info,
    extract_reusable_images,
    extract_tagline,
    extract_testimonials,
    extract_unique_selling_points,
)
from enrichment.conversion import extract_contact_conversion
from enrichment.dental import analyze_dental_treatments
from enrichment.hours import extract_opening_hours
from enrichment.practitioner import extract_practitioners
from enrichment.quality import evaluate_website_quality
from enrichment.social import extract_social_links
from enrichment.technology import detect_website_technology

logger = logging.getLogger("fastui.worker.enrichment.orchestrator")


class WebsiteEnrichmentEngine:
    """
    Lightweight, multi-page website enrichment engine for FastUI.
    """

    def __init__(self, timeout_sec: float = 8.0):
        self.client = EnrichmentHttpClient(timeout_sec=timeout_sec)

    async def enrich_website(self, params: EnrichmentParams) -> EnrichmentResponse:
        """
        Executes multi-page enrichment within a strict budget of high-value pages.
        """
        start_time = time.perf_counter()
        target_url = params.website.strip()
        pages_crawled: List[str] = []

        logger.info(
            f"Starting website enrichment for '{target_url}' (business='{params.business_name}')"
        )

        # 1. Fetch Homepage
        home_html, canonical_url, error = await self.client.fetch_html(target_url)
        if not home_html:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"Enrichment failed to fetch homepage '{target_url}': {error}")
            return EnrichmentResponse(
                success=False,
                status="failed",
                error=error or "Failed to retrieve website HTML",
                profile=None,
                duration_ms=round(duration_ms, 2),
            )

        base_url = canonical_url or target_url
        pages_crawled.append(base_url)

        # 2. Parse Homepage
        soup = BeautifulSoup(home_html, "html.parser")

        # Run extractors on Homepage
        brand = extract_brand_intelligence(soup, base_url)
        contact = extract_contact_conversion(soup, base_url, location_hint=params.location or "")
        social = extract_social_links(soup)
        contact.social_links.update(social)
        treatments = analyze_dental_treatments(soup)
        doctors, primary_doctor = extract_practitioners(soup)
        technology = detect_website_technology(soup, home_html)
        hours = extract_opening_hours(soup)

        # Content and semantic extraction on Homepage
        tagline = extract_tagline(soup, getattr(brand, "brand_name", None) or params.business_name)
        about_text = extract_about_and_mission(soup)
        brand_colors = extract_brand_colors(soup)
        testimonials = extract_testimonials(soup)
        faqs = extract_faqs(soup)
        facilities = extract_facilities_and_amenities(soup)
        certifications = extract_certifications(soup)
        insurance_info = extract_insurance_info(soup)
        emergency_services = extract_emergency_services(soup)
        unique_selling_points = extract_unique_selling_points(soup)
        branches = extract_branches(soup, base_url)
        reusable_images = extract_reusable_images(soup, base_url)

        # 3. High-Value Subpage Discovery
        subpages_to_visit = self._discover_subpages(soup, base_url, max_pages=params.max_pages - 1)

        for page_type, sub_url in subpages_to_visit:
            if sub_url in pages_crawled:
                continue

            try:
                sub_html, _, sub_err = await self.client.fetch_html(sub_url)
                if not sub_html:
                    continue

                pages_crawled.append(sub_url)
                sub_soup = BeautifulSoup(sub_html, "html.parser")

                # Targeted enrichment based on subpage type
                if page_type in ("team", "about"):
                    sub_doctors, sub_prim = extract_practitioners(sub_soup)
                    if sub_doctors:
                        existing_names = {d.name.lower() for d in doctors}
                        doctors.extend(
                            [d for d in sub_doctors if d.name.lower() not in existing_names]
                        )
                        if not primary_doctor and sub_prim:
                            primary_doctor = sub_prim
                    if not about_text:
                        about_text = extract_about_and_mission(sub_soup)
                    if not tagline:
                        tagline = extract_tagline(
                            sub_soup, getattr(brand, "brand_name", None) or params.business_name
                        )
                    # Merge certifications and facilities
                    for c in extract_certifications(sub_soup):
                        if c not in certifications:
                            certifications.append(c)
                    for f in extract_facilities_and_amenities(sub_soup):
                        if f not in facilities:
                            facilities.append(f)

                elif page_type == "services":
                    sub_treatments = analyze_dental_treatments(sub_soup)
                    for k, v in sub_treatments.items():
                        if v.detected:
                            if (
                                k not in treatments
                                or not treatments[k].detected
                                or treatments[k].confidence < v.confidence
                            ):
                                treatments[k] = v
                    for f in extract_facilities_and_amenities(sub_soup):
                        if f not in facilities:
                            facilities.append(f)

                elif page_type == "reviews":
                    sub_testimonials = extract_testimonials(sub_soup)
                    existing_quotes = {t.quote[:40].lower() for t in testimonials}
                    for t in sub_testimonials:
                        if t.quote[:40].lower() not in existing_quotes:
                            testimonials.append(t)
                            existing_quotes.add(t.quote[:40].lower())

                elif page_type == "faqs":
                    sub_faqs = extract_faqs(sub_soup)
                    existing_qs = {q.question.lower() for q in faqs}
                    for q in sub_faqs:
                        if q.question.lower() not in existing_qs:
                            faqs.append(q)
                            existing_qs.add(q.question.lower())

                elif page_type == "insurance":
                    sub_ins = extract_insurance_info(sub_soup)
                    existing_provs = set(insurance_info.get("providers", []))
                    existing_provs.update(sub_ins.get("providers", []))
                    insurance_info["providers"] = sorted(existing_provs)
                    if sub_ins.get("has_emi"):
                        insurance_info["has_emi"] = True
                    if sub_ins.get("has_membership"):
                        insurance_info["has_membership"] = True

                elif page_type in ("contact", "locations"):
                    sub_contact = extract_contact_conversion(
                        sub_soup, base_url, location_hint=params.location or ""
                    )
                    if sub_contact.emails:
                        for e in sub_contact.emails:
                            if e not in contact.emails:
                                contact.emails.append(e)
                    if sub_contact.phones:
                        for p in sub_contact.phones:
                            if p not in contact.phones:
                                contact.phones.append(p)
                    if not contact.whatsapp and sub_contact.whatsapp:
                        contact.whatsapp = sub_contact.whatsapp
                    if not hours:
                        hours = extract_opening_hours(sub_soup)
                    sub_branches = extract_branches(sub_soup, base_url)
                    existing_branch_addrs = {b.address[:30].lower() for b in branches}
                    for b in sub_branches:
                        if b.address[:30].lower() not in existing_branch_addrs:
                            branches.append(b)
                            existing_branch_addrs.add(b.address[:30].lower())

                # Merge any social profiles discovered across subpages (Contact, About, Header/Footer)
                sub_social = extract_social_links(sub_soup)
                for platform, s_url in sub_social.items():
                    if platform not in contact.social_links:
                        contact.social_links[platform] = s_url

                # Accumulate reusable images from subpages
                sub_imgs = extract_reusable_images(sub_soup, sub_url)
                for cat, img_list in sub_imgs.items():
                    current_list = reusable_images.setdefault(cat, [])
                    for u in img_list:
                        if u not in current_list and len(current_list) < 6:
                            current_list.append(u)

            except Exception as e:
                logger.debug(f"Notice visiting subpage '{sub_url}': {e}")

        # Update brand with enriched content fields
        brand.tagline = tagline
        brand.about_text = about_text
        brand.brand_colors = brand_colors

        # 4. Website Quality Evaluation
        quality = evaluate_website_quality(soup, base_url, brand, contact)

        # 5. Assemble Profile
        profile = EnrichedBusinessProfile(
            website_url=target_url,
            canonical_url=canonical_url,
            brand=brand,
            tagline=tagline,
            about_text=about_text,
            brand_colors=brand_colors,
            doctors=doctors,
            primary_doctor=primary_doctor,
            treatments=treatments,
            contact=contact,
            technology=technology,
            quality=quality,
            opening_hours=hours,
            testimonials=testimonials,
            faqs=faqs,
            facilities=facilities,
            certifications=certifications,
            insurance_info=insurance_info,
            emergency_services=emergency_services,
            unique_selling_points=unique_selling_points,
            branches=branches,
            reusable_images=reusable_images,
            pages_crawled=pages_crawled,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Enrichment completed for '{target_url}' in {duration_ms:.1f}ms "
            f"(pages={len(pages_crawled)}, logo={bool(brand.logo_url)}, "
            f"doctor={primary_doctor.name if primary_doctor else None}, score={quality.score})"
        )

        return EnrichmentResponse(
            success=True,
            status="completed" if brand.logo_url and primary_doctor else "partial",
            error=None,
            profile=profile,
            duration_ms=round(duration_ms, 2),
        )

    def _discover_subpages(
        self, soup: BeautifulSoup, base_url: str, max_pages: int = 3
    ) -> List[Tuple[str, str]]:
        """
        Discovers internal links for team, services, reviews, faqs, insurance, and contact pages.
        Returns prioritized list of (page_type, absolute_url).
        """
        target_domain = urlparse(base_url).netloc.lower()
        candidates: Dict[str, str] = {}

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Ensure same domain
            if parsed.netloc.lower() != target_domain:
                continue

            path = parsed.path.lower().strip("/")
            if not path:
                continue

            # Prioritized category checks
            if "team" not in candidates and any(
                k in path
                for k in ("doctor", "dentist", "our-team", "team", "faculty", "specialist")
            ):
                candidates["team"] = full_url
            elif "about" not in candidates and any(
                k in path for k in ("about", "our-story", "who-we-are", "mission", "profile")
            ):
                candidates["about"] = full_url
            elif "services" not in candidates and any(
                k in path for k in ("service", "treatment", "procedure", "specialit")
            ):
                candidates["services"] = full_url
            elif "reviews" not in candidates and any(
                k in path for k in ("review", "testimonial", "patient-story", "feedback")
            ):
                candidates["reviews"] = full_url
            elif "faqs" not in candidates and any(k in path for k in ("faq", "question")):
                candidates["faqs"] = full_url
            elif "insurance" not in candidates and any(
                k in path for k in ("insurance", "payment", "financing", "pricing", "plans")
            ):
                candidates["insurance"] = full_url
            elif "contact" not in candidates and any(
                k in path for k in ("contact", "reach", "location", "branch")
            ):
                candidates["contact"] = full_url
            elif "gallery" not in candidates and any(
                k in path for k in ("gallery", "before-after", "smile-gallery", "cases")
            ):
                candidates["gallery"] = full_url

            if len(candidates) >= max_pages:
                break

        return list(candidates.items())[:max_pages]
