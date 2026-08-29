"""
FastUI Worker Package
=====================
Dedicated scraping, data discovery, and entity normalization subsystem.
"""

from worker.normalizers import BusinessNameNormalizer, NormalizedBusinessName
from worker.contracts import DiscoveredLead, DiscoverySearchParams
from worker.deduplication import LeadDeduplicator

__all__ = [
    "BusinessNameNormalizer",
    "NormalizedBusinessName",
    "DiscoveredLead",
    "DiscoverySearchParams",
    "LeadDeduplicator",
]
