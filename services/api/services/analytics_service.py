from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List

from models.schema import Business, Lead, Activity, PipelineStage
from schemas.stats import DashboardStatsResponse, ActivityFeedItem

class AnalyticsService:
    @staticmethod
    async def get_dashboard_metrics(session: AsyncSession) -> DashboardStatsResponse:
        """
        Aggregates live pipeline KPIs and recent activity events.
        """
        # 1. Pipeline stage KPI counts
        result = await session.execute(
            select(Lead.stage, func.count(Lead.id))
            .group_by(Lead.stage)
        )
        stage_counts = {
            (k.value if hasattr(k, "value") else str(k)).lower(): v
            for k, v in result.all()
        }
        
        new_leads = stage_counts.get("lead", 0)
        follow_ups = stage_counts.get("follow-up", 0) + stage_counts.get("follow_up", 0) + stage_counts.get("contacted", 0)
        proposals_sent = stage_counts.get("proposal", 0) + stage_counts.get("proposal sent", 0)
        
        # 2. Recent activities joined with Business
        activity_result = await session.execute(
            select(Activity, Business.business_name)
            .join(Business, Activity.business_id == Business.id)
            .order_by(desc(Activity.created_at))
            .limit(10)
        )
        
        recent_activities: List[ActivityFeedItem] = []
        for activity, business_name in activity_result:
            time_str = activity.created_at.strftime("%H:%M") if activity.created_at else "Recently"
            act_type = activity.type.value if hasattr(activity.type, 'value') else str(activity.type)
            recent_activities.append(ActivityFeedItem(
                type=act_type,
                target=business_name,
                time=time_str,
                outcome=activity.outcome,
                notes=activity.notes
            ))
            
        if not recent_activities:
            recent_activities = [
                ActivityFeedItem(
                    type="note",
                    target="System",
                    time="Just now",
                    notes="No recent activities recorded."
                )
            ]
            
        return DashboardStatsResponse(
            new_leads=new_leads,
            follow_ups=follow_ups,
            proposals_sent=proposals_sent,
            recent_activities=recent_activities
        )
