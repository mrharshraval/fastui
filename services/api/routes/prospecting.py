from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import EntityNotFoundException
from models.database import get_db
from models.schema import DiscoveryJob, JobStatus
from schemas.prospecting import ProspectingQuery, JobCreateResponse, JobStatusResponse
from schemas.auth import TokenData
from services.auth_service import get_current_user
from services.discovery_service import DiscoveryService

router = APIRouter(prefix="/prospecting", tags=["prospecting"])

@router.post("/jobs", response_model=JobCreateResponse)
async def create_discovery_job(
    query: ProspectingQuery,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Creates a lead discovery job and enqueues the scraping task in the background.
    """
    job = DiscoveryJob(
        query=query.model_dump(),
        status=JobStatus.QUEUED
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    background_tasks.add_task(DiscoveryService.process_job, job.id)
    return JobCreateResponse(job_id=str(job.id), status=job.status.value)

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Polls the status and progress metrics of an active or completed discovery job.
    """
    job = await session.get(DiscoveryJob, job_id)
    if not job:
        raise EntityNotFoundException("DiscoveryJob", job_id)
        
    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status.value,
        progress_percent=job.progress_percent,
        total_discovered=job.total_discovered,
        total_processed=job.total_processed,
        new_leads=job.new_leads,
        existing_businesses=job.existing_businesses,
        duplicates=job.duplicates,
        skipped=job.skipped,
        errors=job.errors,
        error_message=job.error_message
    )

@router.patch("/jobs/{job_id}/cancel", response_model=JobStatusResponse)
async def cancel_discovery_job(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Cancels an ongoing or queued discovery job.
    """
    job = await DiscoveryService.cancel_job(session, job_id)
    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status.value,
        progress_percent=job.progress_percent,
        total_discovered=job.total_discovered,
        total_processed=job.total_processed,
        new_leads=job.new_leads,
        existing_businesses=job.existing_businesses,
        duplicates=job.duplicates,
        skipped=job.skipped,
        errors=job.errors,
        error_message=job.error_message
    )
