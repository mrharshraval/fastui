"""
FastUI Dental Specialty & Semantic Treatment Analyzer
======================================================
Analyzes website text, headings, and structured data across
18 core dental treatment categories, returning confidence-scored signals.
"""

import re
from typing import Dict, List
from bs4 import BeautifulSoup

from contracts import TreatmentSignal

DENTAL_SPECIALTIES_TAXONOMY: Dict[str, List[str]] = {
    "General Dentistry": [
        "general dentistry", "dental checkup", "teeth cleaning", "dental fillings",
        "cavity filling", "preventive dentistry", "oral examination", "dental hygiene", "scaling and polishing"
    ],
    "Cosmetic Dentistry": [
        "cosmetic dentistry", "smile makeover", "aesthetic dentistry", "dental bonding",
        "gum contouring", "enamel shaping", "teeth restoration", "hollywood smile"
    ],
    "Dental Implants": [
        "dental implant", "implants", "all-on-4", "all on 4", "single tooth implant",
        "implantology", "basal implant", "full mouth dental implants", "nobel biocare", "osstem"
    ],
    "Invisalign": [
        "invisalign", "invisalign provider", "invisalign certified", "invisalign braces", "invisalign teen"
    ],
    "Clear Aligners": [
        "clear aligner", "invisible aligner", "invisible braces", "clear teeth aligner", "spark aligners"
    ],
    "Orthodontics": [
        "orthodontics", "orthodontic treatment", "orthodontist", "malocclusion", "bite correction", "palatal expander"
    ],
    "Braces": [
        "metal braces", "ceramic braces", "lingual braces", "self-ligating braces", "traditional braces"
    ],
    "Veneers": [
        "porcelain veneers", "composite veneers", "dental veneers", "laminates", "lumineers"
    ],
    "Teeth Whitening": [
        "teeth whitening", "laser teeth whitening", "bleaching", "zoom whitening", "at-home whitening"
    ],
    "Pediatric Dentistry": [
        "pediatric dentistry", "pedodontist", "children's dentistry", "kids dental", "child dental care", "milk teeth"
    ],
    "Root Canal": [
        "root canal", "root canal treatment", "rct", "single sitting root canal", "pain-free rct"
    ],
    "Endodontics": [
        "endodontics", "endodontist", "dental pulp", "apicoectomy", "pulpectomy"
    ],
    "Oral Surgery": [
        "oral surgery", "oral and maxillofacial", "surgical extraction", "jaw surgery", "bone grafting", "sinus lift"
    ],
    "Wisdom Tooth Extraction": [
        "wisdom tooth", "wisdom tooth removal", "impacted tooth", "third molar extraction"
    ],
    "Emergency Dentistry": [
        "emergency dentistry", "emergency dentist", "emergency dental care", "dental trauma", "broken tooth", "toothache relief", "same-day emergency"
    ],
    "Prosthodontics": [
        "prosthodontics", "dentures", "complete dentures", "partial dentures", "dental crown", "dental bridge", "fixed prosthesis"
    ],
    "Periodontics": [
        "periodontics", "periodontist", "gum disease", "pyorrhea", "gingivitis", "periodontitis", "deep cleaning", "gum flap surgery"
    ],
    "Sedation Dentistry": [
        "sedation dentistry", "sleep dentistry", "painless dentistry", "nitrous oxide", "laughing gas", "iv sedation"
    ],
}


def analyze_dental_treatments(soup: BeautifulSoup) -> Dict[str, TreatmentSignal]:
    """
    Scans website headings, navigation, meta tags, and body text
    against the 18 dental specialty categories.
    """
    signals: Dict[str, TreatmentSignal] = {}

    # Extract text by prominence
    headings = " ".join([h.get_text(separator=" ", strip=True) for h in soup.find_all(["h1", "h2", "h3", "nav"])])
    meta_tags = " ".join([
        meta.get("content", "")
        for meta in soup.find_all("meta", attrs={"name": re.compile(r"description|keywords|services", re.I)})
    ])
    full_body = soup.get_text(separator=" ", strip=True)

    headings_lower = headings.lower()
    meta_lower = meta_tags.lower()
    body_lower = full_body.lower()

    for category, keywords in DENTAL_SPECIALTIES_TAXONOMY.items():
        matched = []
        best_confidence = 0.0
        best_source = None

        for kw in keywords:
            # Check headings first (highest signal confidence)
            if re.search(rf"\b{re.escape(kw)}\b", headings_lower):
                matched.append(kw)
                if best_confidence < 0.90:
                    best_confidence = 0.90
                    best_source = "heading"

            # Check meta description/keywords
            elif re.search(rf"\b{re.escape(kw)}\b", meta_lower):
                matched.append(kw)
                if best_confidence < 0.75:
                    best_confidence = 0.75
                    best_source = "meta"

            # Check body text
            elif re.search(rf"\b{re.escape(kw)}\b", body_lower):
                matched.append(kw)
                if best_confidence < 0.55:
                    best_confidence = 0.55
                    best_source = "body"

        detected = bool(matched)
        signals[category] = TreatmentSignal(
            name=category,
            detected=detected,
            confidence=round(best_confidence, 2) if detected else 0.0,
            source=best_source,
            keywords_matched=list(set(matched))[:5],
        )

    return signals
