"""FastUI Prospecting Domain API Routes.

Exposes endpoints for initiating and monitoring automated business lead discovery jobs.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.models import User
from app.domains.prospecting.schemas import (
    JobCreateResponse,
    JobStatusResponse,
    JobUpdateRequest,
    ProspectingQuery,
)
from app.domains.prospecting.service import ProspectingService

router = APIRouter(prefix="/prospecting", tags=["Prospecting"])


@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Lead Discovery Job",
)
async def create_discovery_job(
    query: ProspectingQuery,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobCreateResponse:
    """Creates a lead discovery scraping job and enqueues background processing."""
    res = await ProspectingService.create_job(
        session=session,
        query=query,
        user=current_user,
    )
    background_tasks.add_task(ProspectingService.process_job, int(res.job_id))
    return res


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Discovery Job Status",
)
async def get_job_status(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    """Polls progress metrics and results of a discovery job."""
    return await ProspectingService.get_job_status(
        session=session,
        job_id=job_id,
    )


@router.patch(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Update Discovery Job Status",
)
async def update_discovery_job(
    job_id: int,
    req: JobUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    """Updates job state (e.g., status='cancelled')."""
    if req.status and req.status.lower() == "cancelled":
        await ProspectingService.cancel_job(session=session, job_id=job_id)
    return await ProspectingService.get_job_status(session=session, job_id=job_id)


@router.patch(
    "/jobs/{job_id}/cancel",
    response_model=JobStatusResponse,
    summary="Cancel Discovery Job",
)
async def cancel_discovery_job(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    """Cancels an active or queued discovery job."""
    await ProspectingService.cancel_job(session=session, job_id=job_id)
    return await ProspectingService.get_job_status(session=session, job_id=job_id)
