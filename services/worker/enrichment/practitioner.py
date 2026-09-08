"""
FastUI Doctor & Practitioner Intelligence Extractor
===================================================
Extracts publicly listed dentists, specialists, qualifications,
and roles from website JSON-LD and team sections.
"""

import json
import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from contracts import EnrichedDoctor

CREDENTIALS_REGEX = re.compile(
    r"\b(BDS|MDS|DDS|DMD|MBBS|MS|FDSRCS|MFDS|FICOI|FAACD|Fellow|Implantologist|Orthodontist|Endodontist|Periodontist|Pedodontist|Oral\s+Surgeon)\b",
    re.I
)

DOCTOR_NAME_REGEX = re.compile(
    r"(?:Dr\.|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",
)


def extract_practitioners(soup: BeautifulSoup) -> Tuple[List[EnrichedDoctor], Optional[EnrichedDoctor]]:
    """
    Extracts doctor candidates from structured data and HTML.
    Returns: (all_doctors, primary_doctor)
    """
    doctors: List[EnrichedDoctor] = []
    seen_names = set()

    # 1. Check JSON-LD Structured Data
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
                graph = item.get("@graph", [item])
                for entity in graph:
                    if not isinstance(entity, dict):
                        continue
                    if entity.get("@type") == "Person" or "employee" in entity or "founder" in entity:
                        person_obj = entity if entity.get("@type") == "Person" else (entity.get("founder") or entity.get("employee"))
                        if isinstance(person_obj, list):
                            person_list = person_obj
                        elif isinstance(person_obj, dict):
                            person_list = [person_obj]
                        else:
                            person_list = []

                        for p in person_list:
                            if not isinstance(p, dict):
                                continue
                            raw_name = p.get("name", "").strip()
                            if raw_name and len(raw_name) > 3:
                                name_clean = raw_name if raw_name.lower().startswith("dr.") else f"Dr. {raw_name}"
                                if name_clean.lower() not in seen_names:
                                    seen_names.add(name_clean.lower())
                                    job_title = p.get("jobTitle") or p.get("description")
                                    doctors.append(EnrichedDoctor(
                                        name=name_clean,
                                        title=job_title[:80] if job_title else "Dental Surgeon",
                                        credentials=_extract_credentials(f"{name_clean} {job_title or ''}"),
                                        bio=p.get("description")[:250] if p.get("description") else None,
                                        is_primary=True if (entity.get("founder") or len(doctors) == 0) else False,
                                        confidence=0.90,
                                        source="json_ld",
                                    ))
        except Exception:
            pass

    # 2. HTML Heading and Card Scan (if JSON-LD had no doctors)
    if not doctors:
        # Search specifically in team/doctor containers first
        team_containers = soup.find_all(
            ["div", "section", "article"],
            attrs={"class": re.compile(r"team|doctor|staff|dentist|about", re.I)}
        )
        search_targets = team_containers if team_containers else [soup]

        for container in search_targets:
            headings = container.find_all(["h1", "h2", "h3", "h4", "strong", "p"])
            for h in headings:
                text = h.get_text(separator=" ", strip=True)
                matches = DOCTOR_NAME_REGEX.findall(text)
                for m in matches:
                    full_name = f"Dr. {m.strip()}"
                    if full_name.lower() not in seen_names and len(m.strip().split()) >= 2:
                        seen_names.add(full_name.lower())
                        # Look for credentials in parent or sibling text
                        parent_text = h.parent.get_text(separator=" ", strip=True) if h.parent else text
                        creds = _extract_credentials(parent_text)
                        
                        # Detect primary doctor signals
                        is_primary = bool(re.search(r"chief|founder|director|lead|head|principal", parent_text, re.I))
                        
                        doctors.append(EnrichedDoctor(
                            name=full_name,
                            title=_extract_doctor_title(parent_text),
                            credentials=creds,
                            bio=_extract_short_bio(parent_text),
                            is_primary=is_primary,
                            confidence=0.75,
                            source="html_heading",
                        ))
                        if len(doctors) >= 5:
                            break
                if len(doctors) >= 5:
                    break

    # Determine primary doctor
    primary_doctor = None
    if doctors:
        # First check if one is explicitly primary
        for d in doctors:
            if d.is_primary:
                primary_doctor = d
                break
        # Fallback to the first doctor
        if not primary_doctor:
            primary_doctor = doctors[0]
            primary_doctor.is_primary = True

    return doctors, primary_doctor


def _extract_credentials(text: str) -> Optional[str]:
    matches = CREDENTIALS_REGEX.findall(text)
    if matches:
        return ", ".join(sorted(list(set(m.upper() for m in matches))))
    return None


def _extract_doctor_title(text: str) -> str:
    lower = text.lower()
    if "chief" in lower or "director" in lower:
        return "Chief Dental Surgeon"
    if "orthodontist" in lower:
        return "Specialist Orthodontist"
    if "implantologist" in lower:
        return "Implantologist & Dental Surgeon"
    if "cosmetic" in lower:
        return "Cosmetic Dental Specialist"
    if "pediatric" in lower or "pedodontist" in lower:
        return "Pediatric Dental Specialist"
    return "Dental Surgeon"


def _extract_short_bio(text: str) -> Optional[str]:
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    for s in sentences:
        if any(term in s.lower() for term in ("experience", "specializ", "fellow", "dentistry", "care", "patient")):
            return f"{s}."
    return None
