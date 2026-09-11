"""FastUI Domain Models Aggregation.

Centralizes metadata registration for all domain entities without circular dependencies.
Imported by Alembic (alembic/env.py) and FastAPI application lifespan for table creation.
"""

from app.domains.auth.models import User, UserRole
from app.domains.businesses.models import Business, BusinessSource, WebsiteStatus
from app.domains.demos.models import DemoEvent, ProspectDemo
from app.domains.engagement.models import (
    Activity,
    ActivityType,
    Contact,
    Interaction,
    InteractionType,
    Note,
    Outreach,
    OutreachChannel,
    OutreachStatus,
    Reminder,
    ReminderStatus,
    Task,
    TaskStatus,
)
from app.domains.enrichment.models import CrawledWebsite
from app.domains.exports.models import ExportJob, ExportStatus
from app.domains.leads.models import Lead, LeadPriority, LeadSignal, PipelineStage
from app.domains.notifications.models import PushSubscription
from app.domains.prospecting.models import DiscoveryJob, JobStatus
from app.infrastructure.database.base import Base, TimestampMixin

__all__ = [
    "Base",
    "TimestampMixin",
    # Auth
    "User",
    "UserRole",
    # Businesses
    "Business",
    "BusinessSource",
    "WebsiteStatus",
    # Leads
    "Lead",
    "LeadPriority",
    "LeadSignal",
    "PipelineStage",
    # Engagement
    "Contact",
    "Note",
    "Task",
    "TaskStatus",
    "Reminder",
    "ReminderStatus",
    "Outreach",
    "OutreachChannel",
    "OutreachStatus",
    "Interaction",
    "InteractionType",
    "Activity",
    "ActivityType",
    # Demos
    "ProspectDemo",
    "DemoEvent",
    # Enrichment
    "CrawledWebsite",
    # Prospecting
    "DiscoveryJob",
    "JobStatus",
    # Exports
    "ExportJob",
    "ExportStatus",
    # Notifications
    "PushSubscription",
]
