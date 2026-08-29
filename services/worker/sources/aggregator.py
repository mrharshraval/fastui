import asyncio
import logging
from typing import List, Optional
from worker.contracts import DiscoverySearchParams, DiscoveredLead
from .base import DiscoverySourceAdapter
from .google_maps import GoogleMapsScraper
from .web_search import WebSearchScraper
from worker.deduplication import normalize_phone, normalize_website

logger = logging.getLogger(__name__)

class MultiSourceDiscoveryAggregator(DiscoverySourceAdapter):
    """
    Orchestrates multi-source discovery across Google Maps, Web Search, and B2B directories.
    Merges duplicate records found across sources and enriches them with multi-source contact details.
    """
    
    def __init__(self, headless: bool = True):
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
            
        # 3. In-memory deduplication and lead enrichment across sources
        merged_leads: List[DiscoveredLead] = []
        seen_keys = set()
        
        for lead in all_leads:
            norm_web = normalize_website(lead.website)
            norm_phone = normalize_phone(lead.phone)
            name_key = lead.name.lower().strip() if lead.name else ""
            
            # Form deduplication key
            dedup_key = norm_web or norm_phone or name_key
            if not dedup_key:
                continue
                
            if dedup_key in seen_keys:
                # Find existing and enrich missing fields
                for existing in merged_leads:
                    existing_key = normalize_website(existing.website) or normalize_phone(existing.phone) or existing.name.lower().strip()
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
                
        logger.info(f"MultiSource Aggregator: Final merged total of {len(merged_leads)} leads (from {len(all_leads)} raw results)")
        return merged_leads
