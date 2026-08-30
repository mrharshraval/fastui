"""
FastUI Multi-Source Discovery Aggregator
========================================
Combines Google Maps and Web Search with in-memory entity resolution.
"""

import logging
from typing import List

from contracts import DiscoveredLead, DiscoverySearchParams
from deduplication import LeadDeduplicator
from sources.base import DiscoverySourceAdapter
from sources.google_maps import GoogleMapsScraper
from sources.web_search import WebSearchScraper

logger = logging.getLogger(__name__)


class MultiSourceDiscoveryAggregator(DiscoverySourceAdapter):
    """
    Orchestrates discovery across Google Maps and Web Search,
    merging and enriching contact details across sources.
    """

    def __init__(self, headless: bool = True) -> None:
        self.google_maps = GoogleMapsScraper(headless=headless)
        self.web_search = WebSearchScraper(headless=headless)

    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        logger.info(f"Starting MultiSource discovery for '{params.target_audience}' in '{params.location}'")

        all_leads: List[DiscoveredLead] = []

        # 1. Primary local discovery via Google Maps
        try:
            maps_leads = await self.google_maps.discover(params)
            all_leads.extend(maps_leads)
            logger.info(f"Google Maps returned {len(maps_leads)} leads.")
        except Exception as e:
            logger.error(f"Google Maps scraper encountered an error: {e}")

        # 2. Secondary discovery / enrichment via Web Search
        try:
            web_leads = await self.web_search.discover(params)
            all_leads.extend(web_leads)
            logger.info(f"Web Search returned {len(web_leads)} leads.")
        except Exception as e:
            logger.error(f"Web Search scraper encountered an error: {e}")

        # 3. In-memory deduplication and cross-source field enrichment
        merged_leads: List[DiscoveredLead] = []
        seen_keys: set = set()

        for lead in all_leads:
            norm_web = LeadDeduplicator.normalize_website(lead.website)
            norm_phone = LeadDeduplicator.normalize_phone(lead.phone)
            name_key = lead.name.lower().strip() if lead.name else ""

            dedup_key = norm_web or norm_phone or name_key
            if not dedup_key:
                continue

            if dedup_key in seen_keys:
                # Enrich the existing record with any new contact signals
                for existing in merged_leads:
                    existing_key = (
                        LeadDeduplicator.normalize_website(existing.website)
                        or LeadDeduplicator.normalize_phone(existing.phone)
                        or existing.name.lower().strip()
                    )
                    if existing_key == dedup_key:
                        if not existing.phone and lead.phone:
                            existing.phone = lead.phone
                        if not existing.website and lead.website:
                            existing.website = lead.website
                        if not existing.email and lead.email:
                            existing.email = lead.email
                        break
            else:
                seen_keys.add(dedup_key)
                merged_leads.append(lead)

        logger.info(
            f"MultiSource Aggregator: {len(merged_leads)} unique businesses from {len(all_leads)} raw results."
        )
        return merged_leads
