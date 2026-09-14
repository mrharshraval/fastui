"""
FastUI Geographic Provider Protocol
===================================
Structural interface for authoritative dynamic locality providers.
"""

from typing import List, Protocol, runtime_checkable

from geo.models import Locality, LocationScope


@runtime_checkable
class GeographicProvider(Protocol):
    """
    Protocol for external authoritative geographic locality providers.
    Enforces async non-blocking resolution and connection lifecycle.
    """

    provider_name: str

    async def fetch_localities(self, scope: LocationScope) -> List[Locality]:
        """Fetches verified geographic localities within the specified scope."""
        ...

    async def aclose(self) -> None:
        """Closes any underlying network connection pools."""
        ...
