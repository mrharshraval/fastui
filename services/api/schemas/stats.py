from pydantic import BaseModel
from typing import List, Optional

class ActivityFeedItem(BaseModel):
    type: str
    target: str
    time: str
    outcome: Optional[str] = None
    notes: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    new_leads: int
    follow_ups: int
    proposals_sent: int
    recent_activities: List[ActivityFeedItem]
