"""
FastUI Multi-Source Discovery Aggregator
========================================
Sequences discovery across Google Maps and Web Search with bounded memory,
cross-source deduplication, field enrichment, and source exhaustion tracking.
"""

import logging
from typing import Dict, List, Tuple

from contracts import DiscoveredLead, DiscoverySearchParams
from deduplication import LeadDeduplicator
from sources.base import DiscoverySourceAdapter
from sources.google_maps import GoogleMapsScraper
from sources.web_search import WebSearchScraper
from utils.memory import memory_tracker

logger = logging.getLogger(__name__)


class MultiSourceDiscoveryAggregator(DiscoverySourceAdapter):
    """
    Orchestrates discovery across enabled sources (Google Maps primary, Web Search secondary).
    Enforces bounded batching, source failure isolation, and per-source exhaustion tracking.
    """

    def __init__(self, headless: bool = True) -> None:
        self.google_maps = GoogleMapsScraper(headless=headless)
        self.web_search = WebSearchScraper(headless=headless)
        self.sources_exhausted: Dict[str, bool] = {
            "google_maps": False,
            "web_search": False,
        }
        self.is_exhausted: bool = False

    async def discover_with_meta(
        self, params: DiscoverySearchParams
    ) -> Tuple[List[DiscoveredLead], bool, Dict[str, bool], float]:
        """
        Executes multi-source discovery and returns leads along with exhaustion and memory metadata.
        """
        leads = await self.discover(params)
        peak_rss = memory_tracker.peak_rss_mb
        return leads, self.is_exhausted, self.sources_exhausted, peak_rss

    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        logger.info(
            f"Starting MultiSource discovery for '{params.target_audience}' in '{params.location}' "
            f"(target={params.limit})"
        )

        all_leads: List[DiscoveredLead] = []
        target_limit = params.limit if params.limit and params.limit > 0 else 50

        # Check source preferences if specified
        enabled_sources = params.source_preferences or ["google_maps", "web_search"]

        # 1. Primary discovery via Google Maps
        if "google_maps" in enabled_sources and len(all_leads) < target_limit:
            if memory_tracker.is_memory_safe():
                try:
                    memory_tracker.log_stage("source_started", source="google_maps")
                    maps_leads = await self.google_maps.discover(params)
                    all_leads.extend(maps_leads)
                    self.sources_exhausted["google_maps"] = getattr(self.google_maps, "is_exhausted", False)
                    logger.info(
                        f"Google Maps returned {len(maps_leads)} leads "
                        f"(exhausted={self.sources_exhausted['google_maps']})."
                    )
                except Exception as e:
                    logger.error(f"Google Maps scraper encountered an error: {e}", exc_info=True)
                    self.sources_exhausted["google_maps"] = True
            else:
                logger.warning("Memory safety limit reached before Google Maps execution.")

        # 2. Secondary discovery / enrichment via Web Search if target remaining or maps exhausted
        if "web_search" in enabled_sources and len(all_leads) < target_limit:
            if memory_tracker.is_memory_safe():
                try:
                    memory_tracker.log_stage("source_started", source="web_search")
                    # Calculate remaining for secondary source
                    secondary_params = params.model_copy()
                    secondary_params.limit = target_limit - len(all_leads)
                    web_leads = await self.web_search.discover(secondary_params)
                    all_leads.extend(web_leads)
                    self.sources_exhausted["web_search"] = getattr(self.web_search, "is_exhausted", False)
                    logger.info(
                        f"Web Search returned {len(web_leads)} leads "
                        f"(exhausted={self.sources_exhausted['web_search']})."
                    )
                except Exception as e:
                    logger.error(f"Web Search scraper encountered an error: {e}", exc_info=True)
                    self.sources_exhausted["web_search"] = True
            else:
                logger.warning("Memory safety limit reached before Web Search execution.")

        # 3. In-memory deduplication and cross-source field enrichment
        merged_leads: List[DiscoveredLead] = []

        for lead in all_leads:
            norm_web = LeadDeduplicator.normalize_website(lead.website)
            norm_phone = LeadDeduplicator.normalize_phone(lead.phone)
            name_key = lead.name.lower().strip() if lead.name else ""

            matched_existing: Optional[DiscoveredLead] = None

            for existing in merged_leads:
                existing_norm_web = LeadDeduplicator.normalize_website(existing.website)
                existing_norm_phone = LeadDeduplicator.normalize_phone(existing.phone)
                existing_name_key = existing.name.lower().strip() if existing.name else ""

                # Check match criteria
                is_match = False
                if lead.source_place_id and existing.source_place_id and lead.source_place_id == existing.source_place_id:
                    is_match = True
                elif norm_web and existing_norm_web and norm_web == existing_norm_web:
                    is_match = True
                elif norm_phone and existing_norm_phone and norm_phone == existing_norm_phone:
                    is_match = True
                elif name_key and existing_name_key and name_key == existing_name_key:
                    is_match = True

                if is_match:
                    matched_existing = existing
                    break

            if matched_existing:
                # Enrich existing record
                if not matched_existing.phone and lead.phone:
                    matched_existing.phone = lead.phone
                if not matched_existing.website and lead.website:
                    matched_existing.website = lead.website
                if not matched_existing.email and lead.email:
                    matched_existing.email = lead.email
                if not matched_existing.address and lead.address:
                    matched_existing.address = lead.address
                if not matched_existing.source_place_id and lead.source_place_id:
                    matched_existing.source_place_id = lead.source_place_id
            else:
                merged_leads.append(lead)


        # Cap results to target_limit
        final_leads = merged_leads[:target_limit]

        # Determine overall exhaustion
        all_enabled_exhausted = all(
            self.sources_exhausted.get(src, True) for src in enabled_sources
        )
        self.is_exhausted = all_enabled_exhausted or (len(final_leads) < target_limit)

        logger.info(
            f"MultiSource Aggregator: {len(final_leads)} unique businesses from {len(all_leads)} raw results. "
            f"(exhausted={self.is_exhausted})"
        )
        memory_tracker.log_stage(
            "discovery_complete",
            extra={"unique_count": str(len(final_leads)), "exhausted": str(self.is_exhausted)},
        )

        return final_leads
