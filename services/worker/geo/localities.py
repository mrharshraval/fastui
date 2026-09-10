"""
FastUI Dynamic Geographic Locality Resolution Engine
===================================================
Discovers real city localities, suburbs, neighbourhoods, and commercial zones
dynamically for any city worldwide using OpenStreetMap (Nominatim and Overpass API).

Key Features:
- Multi-tier, paginated discovery across settlement types (suburbs, neighbourhoods, quarters).
- Dynamic subdivision of dense commercial zones to explore distinct micro-pockets.
- Two-level caching (in-memory + persistent disk cache) for instant sub-millisecond lookups.
- Curated registry preserved strictly as an optional fallback / manual override.
- Directional sector partitioning fallback for offline or unlisted environments.
"""

import json
import logging
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Set
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_FILE = CACHE_DIR / "localities_cache.json"

USER_AGENT = "FastUI-DiscoveryWorker/1.0 (local.dev)"
REQUEST_TIMEOUT = 7.0

# Curated commercial, retail, and medical locality registries for major cities (optional fallback/override)
CITY_LOCALITY_REGISTRY: Dict[str, List[str]] = {
    "ahmedabad": [
        "Navrangpura",
        "Satellite",
        "Bodakdev",
        "Vastrapur",
        "Thaltej",
        "Bopal",
        "South Bopal",
        "Prahlad Nagar",
        "SG Highway",
        "Ambawadi",
        "Jodhpur",
        "Chandkheda",
        "Motera",
        "Sabarmati",
        "Gota",
        "Ranip",
        "New CG Road",
        "Tragad",
        "Maninagar",
        "Nikol",
        "Naroda",
        "Odhav",
        "Vastral",
        "Isanpur",
        "Paldi",
        "Ellisbridge",
        "Ashram Road",
        "Usmanpura",
        "Shahibaug",
        "Naranpura",
        "Memnagar",
        "Ghatlodia",
        "Sola",
        "Science City",
        "Sindhu Bhavan Road",
    ],
    "mumbai": [
        "Andheri West",
        "Andheri East",
        "Bandra West",
        "Bandra East",
        "Juhu",
        "Santacruz",
        "Khar",
        "Powai",
        "Goregaon",
        "Malad",
        "Kandivali",
        "Borivali",
        "Dadar",
        "Lower Parel",
        "Worli",
        "Colaba",
        "Nariman Point",
        "Fort",
        "Chembur",
        "Ghatkopar",
        "Mulund",
        "Kurla",
        "Vashi",
        "Thane West",
    ],
    "delhi": [
        "Connaught Place",
        "South Extension",
        "Lajpat Nagar",
        "Hauz Khas",
        "Greater Kailash",
        "Saket",
        "Vasant Kunj",
        "Dwarka",
        "Rohini",
        "Pitampura",
        "Janakpuri",
        "Rajouri Garden",
        "Karol Bagh",
        "Chandni Chowk",
        "Laxmi Nagar",
        "Preet Vihar",
        "Mayur Vihar",
        "Model Town",
        "Civil Lines",
        "Nehru Place",
    ],
    "bangalore": [
        "Koramangala",
        "Indiranagar",
        "HSR Layout",
        "Whitefield",
        "Jayanagar",
        "JP Nagar",
        "Electronic City",
        "BTM Layout",
        "Marathahalli",
        "Malleshwaram",
        "Rajajinagar",
        "Banashankari",
        "Hebbal",
        "Yelahanka",
        "Bellandur",
        "Sarjapur Road",
        "MG Road",
        "Kalyan Nagar",
        "Basavanagudi",
        "Sadashivanagar",
    ],
    "hyderabad": [
        "Banjara Hills",
        "Jubilee Hills",
        "Hitec City",
        "Gachibowli",
        "Madhapur",
        "Kondapur",
        "Kukatpally",
        "Ameerpet",
        "Begumpet",
        "Secunderabad",
        "Dilsukhnagar",
        "LB Nagar",
        "Miyapur",
        "Manikonda",
        "Somajiguda",
        "Panjagutta",
        "Abids",
        "Koti",
    ],
    "pune": [
        "Kothrud",
        "Baner",
        "Aundh",
        "Viman Nagar",
        "Kalyani Nagar",
        "Koregaon Park",
        "Hinjewadi",
        "Wakad",
        "Hadapsar",
        "Magarpatta",
        "Shivajinagar",
        "Deccan Gymkhana",
        "Camp",
        "FC Road",
        "JM Road",
        "Pimple Saudagar",
        "Bavdhan",
        "Kondhwa",
    ],
    "chennai": [
        "T Nagar",
        "Adyar",
        "Besant Nagar",
        "Anna Nagar",
        "Mylapore",
        "Velachery",
        "Nungambakkam",
        "Alwarpet",
        "Kilpauk",
        "OMR Thoraipakkam",
        "Sholinganallur",
        "Guindy",
        "Porur",
        "Tambaram",
        "Chromepet",
    ],
    "kolkata": [
        "Park Street",
        "Salt Lake Sector 1",
        "Salt Lake Sector 5",
        "New Town",
        "Ballygunge",
        "Alipore",
        "Gariahat",
        "Bhowanipore",
        "Shyambazar",
        "Howrah",
        "Behala",
        "Jadavpur",
        "Tollygunge",
        "Dum Dum",
        "Kankurgachi",
        "Ruby EM Bypass",
    ],
    "surat": [
        "Adajan",
        "Vesu",
        "Pal",
        "Varachha",
        "Katargam",
        "Ghod Dod Road",
        "Piplod",
        "Athwalines",
        "City Light",
        "Rander",
        "Udhna",
        "Majura Gate",
    ],
    "jaipur": [
        "Malviya Nagar",
        "Vaishali Nagar",
        "C Scheme",
        "Mansarovar",
        "Raja Park",
        "Tonk Road",
        "MI Road",
        "Bani Park",
        "Jagatpura",
        "Vidhyadhar Nagar",
    ],
    "chandigarh": [
        "Sector 17",
        "Sector 35",
        "Sector 22",
        "Sector 8",
        "Sector 9",
        "Sector 26",
        "Sector 43",
        "Sector 70 Mohali",
        "Phase 7 Mohali",
        "Panchkula Sector 20",
    ],
}


def clean_city_name(location: str) -> str:
    """
    Extracts the primary city name from a location string.
    Example: 'Ahmedabad, Gujarat, India' -> 'ahmedabad'
    """
    if not location:
        return ""
    first_part = location.split(",")[0].strip().lower()
    cleaned = re.sub(r"\b(city|district|metro|area|region)\b", "", first_part).strip()
    return cleaned


class DynamicLocalityResolver:
    """
    Resolves city localities dynamically using OpenStreetMap / Nominatim and Overpass API.
    Provides multi-tier paginated settlement extraction and caching.
    """

    _instance: Optional["DynamicLocalityResolver"] = None

    def __init__(self) -> None:
        self._memory_cache: Dict[str, List[str]] = {}
        self._load_disk_cache()

    @classmethod
    def get_instance(cls) -> "DynamicLocalityResolver":
        if cls._instance is None:
            cls._instance = DynamicLocalityResolver()
        return cls._instance

    def _load_disk_cache(self) -> None:
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._memory_cache.update(data)
                        logger.debug(f"Loaded {len(data)} cached cities from {CACHE_FILE}")
        except Exception as e:
            logger.debug(f"Could not load locality disk cache: {e}")

    def _save_disk_cache(self, key: str, localities: List[str]) -> None:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self._memory_cache[key] = localities
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"Could not persist locality cache for '{key}': {e}")

    def _query_nominatim_tier(
        self,
        query_phrase: str,
        page: int = 1,
        expected_city: str = "",
        expected_country: Optional[str] = None
    ) -> List[str]:
        """
        Executes a single paginated Nominatim search query with strict geographic validation.
        Rejects any matches that do not genuinely belong to the target city and country.
        """
        params = {
            "q": query_phrase,
            "format": "json",
            "limit": "50",
            "addressdetails": "1"
        }
        if page > 1:
            params["offset"] = str((page - 1) * 50)

        url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        names: List[str] = []
        if isinstance(data, list):
            for item in data:
                display_name = item.get("display_name", "")
                address = item.get("address", {}) or {}

                # Strict geographic verification: Must belong to target city or district
                if expected_city:
                    ec_lower = expected_city.lower()
                    dn_lower = display_name.lower()
                    city_matched = (
                        ec_lower in dn_lower or
                        ec_lower in address.get("city", "").lower() or
                        ec_lower in address.get("state_district", "").lower() or
                        ec_lower in address.get("county", "").lower() or
                        ec_lower in address.get("state", "").lower()
                    )
                    if not city_matched:
                        continue

                # Strict country verification
                if expected_country:
                    country_needle = expected_country.lower()
                    dn_lower = display_name.lower()
                    country_matched = (
                        country_needle in dn_lower or
                        country_needle in address.get("country", "").lower()
                    )
                    if not country_matched:
                        continue

                raw_name = item.get("name") or (display_name.split(",")[0])
                if not raw_name:
                    continue
                clean = clean_unicode_spaces(raw_name)
                # Filter out pure numbers, highway codes (e.g. NH 48), or single characters
                if len(clean) >= 3 and not re.match(r"^(NH|SH|State Highway|National Highway|\d+)", clean, re.I):
                    names.append(clean)

        return names

    def fetch_nominatim_iterative(self, city: str, country: Optional[str] = None) -> List[str]:
        """
        Paginates across multiple settlement categories in Nominatim until no new localities appear.
        """
        location_scope = f"{city}, {country}" if country else city
        categories = [
            f"suburbs in {location_scope}",
            f"neighbourhoods in {location_scope}",
            f"commercial areas in {location_scope}",
            f"quarters in {location_scope}",
        ]

        seen_lower: Set[str] = set()
        city_lower = city.lower()
        results: List[str] = []

        for category_query in categories:
            for page in range(1, 3):  # Fetch up to 2 pages per category (up to 100 items each)
                try:
                    page_names = self._query_nominatim_tier(
                        category_query,
                        page=page,
                        expected_city=city,
                        expected_country=country
                    )
                    if not page_names:
                        break

                    new_in_page = 0
                    for name in page_names:
                        nl = name.lower()
                        # Avoid adding the whole city name itself or already seen names
                        if nl != city_lower and nl not in seen_lower:
                            seen_lower.add(nl)
                            results.append(name)
                            new_in_page += 1

                    # If page yielded zero new unique names, move to next category
                    if new_in_page == 0:
                        break
                except Exception as e:
                    logger.debug(f"Nominatim query failed for '{category_query}' p{page}: {e}")
                    break

        return results

    def fetch_overpass(self, city: str) -> List[str]:
        """
        Queries Overpass API across mirrors for settlement tags within the city area.
        """
        mirrors = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
        ]

        ql = f"""[out:json][timeout:8];
area["name"="{city}"]->.city;
(
  node["place"~"^(suburb|neighbourhood|quarter|town|city_block)$"](area.city);
  way["place"~"^(suburb|neighbourhood|quarter|town|city_block)$"](area.city);
);
out tags 75;
"""
        encoded_data = urllib.parse.urlencode({"data": ql}).encode("utf-8")

        for mirror in mirrors:
            try:
                req = urllib.request.Request(
                    mirror,
                    data=encoded_data,
                    headers={"User-Agent": USER_AGENT}
                )
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                elements = data.get("elements", [])
                names: List[str] = []
                seen_lower: Set[str] = set()
                city_lower = city.lower()

                for e in elements:
                    name = e.get("tags", {}).get("name")
                    if name and len(name) >= 3:
                        nl = name.lower()
                        if nl != city_lower and nl not in seen_lower:
                            seen_lower.add(nl)
                            names.append(name)

                if len(names) >= 5:
                    return names
            except Exception as e:
                logger.debug(f"Overpass mirror {mirror} failed for '{city}': {e}")

        return []

    def subdivide_dense_areas(self, localities: List[str], city_name: str) -> List[str]:
        """
        Identifies dense or prominent commercial hubs and introduces micro-subdivisions
        (e.g., East, West, Extension, Commercial Center) so businesses in distinct micro-pockets are reached.
        """
        subdivided: List[str] = []
        seen: Set[str] = set()

        for loc in localities:
            if loc.lower() not in seen:
                seen.add(loc.lower())
                subdivided.append(loc)

            # If locality represents a major known or designated commercial center, add directional sub-pockets
            loc_lower = loc.lower()
            if any(term in loc_lower for term in ("road", "highway", "sector", "square", "chowk", "circle")):
                for sub_suffix in ("East", "West"):
                    sub_name = f"{loc} {sub_suffix}"
                    if sub_name.lower() not in seen:
                        seen.add(sub_name.lower())
                        subdivided.append(sub_name)

        return subdivided

    def resolve(self, location: str) -> List[str]:
        """
        Resolves a location string into an exhaustive list of constituent geographic areas.
        1. Cache lookup
        2. Dynamic OSM / Nominatim iterative multi-tier search
        3. Overpass API settlement query fallback
        4. Optional curated registry fallback / override
        5. Directional sector fallback
        """
        if not location:
            return []

        cleaned_city = clean_city_name(location)
        base_city_display = location.split(",")[0].strip()
        cache_key = cleaned_city

        # 1. Check in-memory & persistent cache
        if cache_key in self._memory_cache and self._memory_cache[cache_key]:
            logger.debug(f"Locality cache hit for '{cache_key}': {len(self._memory_cache[cache_key])} areas")
            return self._memory_cache[cache_key]

        # Check if city has a verified curated registry
        curated_areas: List[str] = []
        for reg_key, localities in CITY_LOCALITY_REGISTRY.items():
            if reg_key in cleaned_city or cleaned_city in reg_key:
                curated_areas = list(localities)
                break

        parts = [p.strip() for p in location.split(",")]
        country = parts[-1] if len(parts) >= 2 else None

        discovered: List[str] = list(curated_areas)
        seen_lower = {d.lower() for d in discovered}

        # 2. Query Overpass API (boundary-contained within city area)
        try:
            overpass_results = self.fetch_overpass(base_city_display)
            for item in overpass_results:
                if item.lower() not in seen_lower:
                    seen_lower.add(item.lower())
                    discovered.append(item)
        except Exception as e:
            logger.debug(f"Overpass resolution exception for '{location}': {e}")

        # 3. Dynamic OSM Nominatim Iterative Search (with strict geographic verification)
        if len(discovered) < 25:
            try:
                nom_results = self.fetch_nominatim_iterative(base_city_display, country=country)
                for item in nom_results:
                    if item.lower() not in seen_lower:
                        seen_lower.add(item.lower())
                        discovered.append(item)
            except Exception as e:
                logger.debug(f"Dynamic Nominatim resolution exception for '{location}': {e}")

        # 4. If dynamic OSM or curated produced valid areas, subdivide dense areas, cache, and return
        if len(discovered) >= 5:
            final_areas = self.subdivide_dense_areas(discovered, base_city_display)
            self._save_disk_cache(cache_key, final_areas)
            logger.info(f"Resolved {len(final_areas)} geographic areas for '{location}'.")
            return final_areas

        # 5. Directional Sector Fallback (Final Safety Net)
        logger.info(f"Using directional sector fallback for unlisted '{location}'.")
        directional_sectors = [
            f"Central {base_city_display}",
            f"North {base_city_display}",
            f"South {base_city_display}",
            f"East {base_city_display}",
            f"West {base_city_display}",
            f"{base_city_display} Suburbs",
            f"Downtown {base_city_display}",
            f"Old {base_city_display}",
        ]
        self._save_disk_cache(cache_key, directional_sectors)
        return directional_sectors


def clean_unicode_spaces(text: str) -> str:
    """Removes non-breaking spaces and collapses whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ").replace("\u200b", " ")).strip()


def resolve_city_localities(location: str) -> List[str]:
    """
    Public API: Resolves a location string into an ordered list of constituent localities/zones.
    Seamlessly feeds into GoogleMapsScraper and discovery pipeline.
    """
    return DynamicLocalityResolver.get_instance().resolve(location)
