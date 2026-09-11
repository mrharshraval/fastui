"""FastUI Analytics Domain Schemas & DTOs."""

from pydantic import BaseModel


class ActivityFeedItem(BaseModel):
    type: str
    target: str
    time: str
    outcome: str | None = None
    notes: str | None = None


class DashboardStatsResponse(BaseModel):
    new_leads: int
    follow_ups: int
    proposals_sent: int
    recent_activities: list[ActivityFeedItem]
