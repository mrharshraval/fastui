"""FastUI Enrichment Domain API Routes.

Exposes asynchronous website intelligence extraction and audit inspection endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.models import User
from app.domains.businesses.models import Business
from app.domains.enrichment.schemas import (
    BusinessEnrichmentStatusResponse,
    EnrichmentTriggerResponse,
)
from app.domains.enrichment.service import EnrichmentService

router = APIRouter(tags=["Enrichment"])


@router.post(
    "/businesses/{business_id}/enrichment",
    response_model=EnrichmentTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Business Website Enrichment",
)
async def trigger_business_enrichment(
    business_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EnrichmentTriggerResponse:
    """Triggers asynchronous website enrichment for a business."""
    business = await session.get(Business, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    if not business.website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business does not have a website URL to enrich",
        )

    background_tasks.add_task(
        EnrichmentService.enrich_business_background,
        business_id=business.id,
    )

    return EnrichmentTriggerResponse(
        business_id=business.id,
        status="queued",
        message=f"Enrichment task queued for {business.website}",
    )


@router.get(
    "/businesses/{business_id}/enrichment",
    response_model=BusinessEnrichmentStatusResponse,
    summary="Get Business Enrichment Profile",
)
async def get_business_enrichment(
    business_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessEnrichmentStatusResponse:
    """Fetches the enriched profile and quality audit results for a business."""
    return await EnrichmentService.get_business_enrichment_status(
        session=session,
        business_id=business_id,
    )
