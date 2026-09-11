"""FastUI Analytics Domain API Routes.

Exposes endpoints for dashboard rollups, pipeline KPIs, and recent activity streams.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.analytics.schemas import DashboardStatsResponse
from app.domains.analytics.service import AnalyticsService
from app.domains.auth.models import User

router = APIRouter(prefix="/stats", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardStatsResponse,
    summary="Get Dashboard Statistics",
)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    """Returns pipeline KPI summary and recent activity feed."""
    return await AnalyticsService.get_dashboard_metrics(session=session)
