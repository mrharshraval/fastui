"""FastUI Pipeline Board API Route Endpoints."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.schemas import TokenData
from app.domains.pipeline.schemas import PipelineDealResponse
from app.domains.pipeline.service import PipelineService

router = APIRouter(tags=["pipeline"])


@router.get("/pipeline", response_model=list[PipelineDealResponse])
async def get_pipeline(
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Returns active sales pipeline leads formatted for the Kanban board view."""
    return await PipelineService.get_pipeline_deals(session=session)
