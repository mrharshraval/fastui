from abc import ABC, abstractmethod
try:
    from worker.contracts import DiscoverySearchParams, DiscoveredLead
except ImportError:
    from contracts import DiscoverySearchParams, DiscoveredLead

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
