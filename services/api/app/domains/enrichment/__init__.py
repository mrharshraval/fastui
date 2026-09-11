"""FastUI Enrichment Domain."""

from app.domains.enrichment.models import CrawledWebsite
from app.domains.enrichment.service import EnrichmentService

__all__ = ["CrawledWebsite", "EnrichmentService"]
