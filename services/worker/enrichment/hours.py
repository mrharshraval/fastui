"""
FastUI Operating Hours Extractor
================================
Extracts structured weekly clinic hours from JSON-LD openingHoursSpecification
or semantic HTML tables/sections.
"""

import json
import re
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup

DAYS_OF_WEEK = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def extract_opening_hours(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extracts structured clinic hours from JSON-LD or semantic HTML.
    """
    # 1. JSON-LD openingHoursSpecification
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
                    
                    # Array of openingHoursSpecification
                    specs = entity.get("openingHoursSpecification")
                    if specs and isinstance(specs, list):
                        hours_dict = {}
                        for spec in specs:
                            if not isinstance(spec, dict):
                                continue
                            day = spec.get("dayOfWeek")
                            opens = spec.get("opens")
                            closes = spec.get("closes")
                            if day:
                                day_str = day if isinstance(day, str) else str(day)
                                day_clean = day_str.split("/")[-1].capitalize()
                                hours_dict[day_clean] = f"{opens or ''} - {closes or ''}".strip(" -")
                        if hours_dict:
                            return hours_dict

                    # String array openingHours: ["Mo-Fr 09:00-18:00", "Sa 09:00-14:00"]
                    raw_hours = entity.get("openingHours")
                    if raw_hours:
                        if isinstance(raw_hours, list):
                            return {"schedule": ", ".join(str(h) for h in raw_hours)}
                        elif isinstance(raw_hours, str):
                            return {"schedule": raw_hours}
        except Exception:
            pass

    # 2. HTML Table or list with days of the week
    hours_containers = soup.find_all(["table", "ul", "div"], attrs={"class": re.compile(r"hours|opening|timing|schedule", re.I)})
    for container in hours_containers:
        text = container.get_text(separator=" ", strip=True)
        if any(d in text for d in ("Monday", "Mon", "Friday", "Fri")):
            # Compact schedule string
            clean_sched = re.sub(r"\s+", " ", text)[:200].strip()
            return {"schedule": clean_sched}

    return None
