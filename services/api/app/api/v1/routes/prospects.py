"""FastUI Prospects API Route Endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.schemas import TokenData
from app.domains.businesses.schemas import BusinessResponse
from app.domains.prospects.schemas import (
    BulkQualifyRequest,
    BulkQualifyResponse,
    QualifyProspectRequest,
)
from app.domains.prospects.service import ProspectsService

router = APIRouter(tags=["prospects"])


@router.get("/prospects", response_model=list[BusinessResponse])
async def list_prospects(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    qualification_status: str | None = Query(None, description="Filter by qualification status"),
    search: str | None = Query(None, description="Search across business name, category, and city"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fetches businesses that have not yet been promoted to active sales leads."""
    return await ProspectsService.list_prospects(
        session=session,
        skip=skip,
        limit=limit,
        qualification_status=qualification_status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.patch("/prospects", response_model=BulkQualifyResponse)
async def update_prospects(
    req: BulkQualifyRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Bulk updates qualification status for selected prospects."""
    return await ProspectsService.bulk_qualify_prospects(
        session=session,
        business_ids=req.business_ids,
        qualification_status=req.qualification_status,
        user_id=current_user.user_id,
    )


@router.patch("/prospects/{business_id}", response_model=BusinessResponse)
async def qualify_prospect(
    business_id: int,
    req: QualifyProspectRequest,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Updates qualification status for a single prospect."""
    return await ProspectsService.qualify_prospect(
        session=session,
        business_id=business_id,
        qualification_status=req.qualification_status,
        user_id=current_user.user_id,
    )
