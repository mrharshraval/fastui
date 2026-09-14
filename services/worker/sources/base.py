from typing import List, Protocol, runtime_checkable

from contracts.discovery import DiscoveredLead, DiscoverySearchParams


@runtime_checkable
class DiscoverySourceAdapter(Protocol):
    """
    Structural protocol for all Lead Discovery source adapters (Google Maps, Web Search, etc.).
    Favors composition over inheritance.
    """

    async def discover(self, params: DiscoverySearchParams) -> List[DiscoveredLead]:
        """Discovers and extracts leads matching the given search parameters."""
        ...

