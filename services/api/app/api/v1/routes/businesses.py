"""FastUI Business API Route Endpoints."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.schemas import TokenData
from app.domains.businesses.schemas import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    BusinessResponse,
    BusinessUpdateRequest,
)
from app.domains.businesses.service import BusinessService

router = APIRouter(tags=["businesses"])


@router.get("/businesses", response_model=list[BusinessResponse])
async def list_businesses(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    is_lead: bool | None = Query(
        None, description="Filter by lead status (true for leads, false for prospects)"
    ),
    stage: str | None = Query(None, description="Filter by pipeline stage"),
    search: str | None = Query(None, description="Search across business name, category, and city"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Lists business accounts across the system with optional lead status, stage, and search filters."""
    return await BusinessService.list_businesses(
        session=session,
        skip=skip,
        limit=limit,
        is_lead=is_lead,
        stage=stage,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fetches details for a single business entity."""
    return await BusinessService.get_business_by_id(session=session, business_id=business_id)


@router.patch("/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    req: BusinessUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Updates core business information, contact data, or qualification status."""
    return await BusinessService.update_business(
        session=session,
        business_id=business_id,
        req=req,
        user_id=current_user.user_id,
    )


@router.delete(
    "/businesses/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Business",
)
async def delete_business(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Response:
    """Atomically deletes a business record and all related cascade entities."""
    await BusinessService.delete_business(
        session=session,
        business_id=business_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/businesses", response_model=BulkDeleteResponse)
async def bulk_delete_businesses(
    req: BulkDeleteRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Atomically deletes multiple selected business records and their cascade entities."""
    return await BusinessService.bulk_delete_businesses(
        session=session,
        business_ids=req.business_ids,
    )
