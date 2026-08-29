import asyncio
import logging
from typing import List

from worker.contracts import DiscoverySearchParams, DiscoveredLead
from .base import DiscoverySourceAdapter

logger = logging.getLogger(__name__)

class MockSourceAdapter(DiscoverySourceAdapter):
    """
    Mock source adapter for development and testing.
    """
    
    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        logger.info(f"Mock Source: Searching for '{params.target_audience}' in '{params.location}'")
        await asyncio.sleep(0.5) # Simulate network latency
        
        return [
            DiscoveredLead(
                name=f"Premier {params.target_audience} Center",
                category=params.target_audience,
                city=params.location,
                phone="+91 98765 00001",
                website="https://premier-example.com",
                source_platform="mock",
                source_url="https://mock.fastui.in/1"
            ),
            DiscoveredLead(
                name=f"{params.location} {params.target_audience} Care",
                category=params.target_audience,
                city=params.location,
                phone="+91 98765 00002",
                website=None, # Simulating No Website
                source_platform="mock",
                source_url="https://mock.fastui.in/2"
            )
        ]
