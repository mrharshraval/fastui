"""FastUI Prospecting Domain."""

from app.domains.prospecting.models import DiscoveryJob, JobStatus
from app.domains.prospecting.service import ProspectingService

__all__ = ["DiscoveryJob", "JobStatus", "ProspectingService"]
