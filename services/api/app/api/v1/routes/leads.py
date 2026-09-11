"""FastUI Sales Leads API Route Endpoints."""

from typing import Any, Union

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.schemas import TokenData
from app.domains.businesses.schemas import BusinessResponse
from app.domains.leads.schemas import (
    BulkAddToLeadsResponse,
    BulkStageRequest,
    BulkStageResponse,
    LeadCreateRequest,
)
from app.domains.leads.service import LeadService
from app.shared.exceptions import ValidationError

router = APIRouter(tags=["leads"])


@router.get("/leads", response_model=list[BusinessResponse])
async def list_leads(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    stage: str | None = Query(None, description="Filter by pipeline stage"),
    search: str | None = Query(None, description="Search across business name, category, and city"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fetches all businesses that have been promoted into the active sales pipeline."""
    return await LeadService.list_leads(
        session=session,
        skip=skip,
        limit=limit,
        stage=stage,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "/leads",
    response_model=Union[BusinessResponse, BulkAddToLeadsResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Promote to Lead",
)
async def create_leads(
    req: LeadCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Promotes one or more prospect records into active sales leads."""
    if req.business_ids:
        return await LeadService.bulk_promote_to_leads(
            session=session,
            business_ids=req.business_ids,
            user_id=current_user.user_id,
        )

    if req.business_id:
        return await LeadService.promote_to_lead(
            session=session,
            business_id=req.business_id,
            user_id=current_user.user_id,
        )

    raise ValidationError("Either 'business_id' or 'business_ids' must be provided.")


@router.patch("/leads", response_model=BulkStageResponse)
async def bulk_update_lead_stages(
    req: BulkStageRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> dict[str, Any]:
    """Bulk updates pipeline stage for multiple sales leads."""
    return await LeadService.bulk_update_stage(
        session=session,
        business_ids=req.business_ids,
        stage=req.stage,
        user_id=current_user.user_id,
    )
