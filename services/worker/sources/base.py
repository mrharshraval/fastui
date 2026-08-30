from abc import ABC, abstractmethod
from typing import List

from contracts import DiscoverySearchParams, DiscoveredLead


class DiscoverySourceAdapter(ABC):
    """
    Abstract interface for all Lead Discovery source adapters (Google Maps, web search, etc.).
    """

    @abstractmethod
    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """
        Discovers and extracts leads matching the given search parameters.
        """
        pass
