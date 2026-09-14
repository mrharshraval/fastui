"""
FastUI Locality In-Memory Bounded Cache
=======================================
Transient in-memory cache with TTL expiration.
Explicitly avoids permanent disk caching or stale persisted files.
"""

import time
from typing import Dict, List, Optional, Tuple

from geo.models import Locality


class LocalityCache:
    """
    In-memory, TTL-expiring cache for resolved localities.
    Never persists to disk; bounded to prevent memory growth.
    """

    def __init__(
        self,
        default_ttl_seconds: float = 86400.0,
        max_entries: int = 500,
    ) -> None:
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self._cache: Dict[str, Tuple[List[Locality], float]] = {}

    def get(self, key: str) -> Optional[List[Locality]]:
        """Retrieves cached localities if not expired."""
        norm_key = key.lower().strip()
        item = self._cache.get(norm_key)
        if not item:
            return None

        localities, expires_at = item
        if time.time() > expires_at:
            del self._cache[norm_key]
            return None

        return list(localities)

    def set(
        self,
        key: str,
        localities: List[Locality],
        ttl_seconds: Optional[float] = None,
    ) -> None:
        """Stores localities in memory with an expiration timestamp."""
        norm_key = key.lower().strip()

        # Simple eviction if at capacity
        if len(self._cache) >= self.max_entries and norm_key not in self._cache:
            # Evict earliest expiring item
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[norm_key] = (list(localities), time.time() + ttl)

    def clear(self) -> None:
        """Purges all entries from memory."""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)
