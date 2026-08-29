from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from schemas.stats import DashboardStatsResponse
from schemas.auth import TokenData
from services.auth_service import get_current_user
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/stats", tags=["dashboard"])

@router.get("", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> DashboardStatsResponse:
    """
    Returns pipeline KPI summary and recent activity feed.
    """
    return await AnalyticsService.get_dashboard_metrics(session)
