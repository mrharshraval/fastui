from abc import ABC, abstractmethod
from typing import List
from worker.contracts import DiscoverySearchParams, DiscoveredLead

class DiscoverySourceAdapter(ABC):
    """
    Abstract interface for all Lead Discovery source adapters (Google Maps, Apollo, etc.).
    """
    
    @abstractmethod
    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """
        Discovers and extracts leads matching the given search parameters.
        """
        pass
