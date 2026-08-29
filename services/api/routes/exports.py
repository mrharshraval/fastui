import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.schema import ExportJob, ExportStatus
from schemas.exports import ExportCreateResponse, ExportStatusResponse
from schemas.auth import TokenData
from services.auth_service import get_current_user
from services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])

@router.post("", response_model=ExportCreateResponse)
@router.post("/", response_model=ExportCreateResponse)
async def create_export(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Enqueues an asynchronous CSV export of all pipeline leads.
    """
    export_id = str(uuid.uuid4())
    job = ExportJob(
        id=export_id,
        status=ExportStatus.QUEUED,
        progress_percent=0,
        records_processed=0,
        total_records=0
    )
    session.add(job)
    await session.commit()
    
    background_tasks.add_task(ExportService.process_export, export_id)
    return ExportCreateResponse(export_id=export_id, message="Export job queued")

@router.get("/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Checks the progress status and download readiness of an export job.
    """
    job = await session.get(ExportJob, export_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job {export_id} not found"
        )
        
    return ExportStatusResponse(
        id=job.id,
        status=job.status.value,
        progress_percent=job.progress_percent,
        records_processed=job.records_processed,
        total_records=job.total_records,
        download_url=job.download_url,
        error_message=job.error_message,
        created_at=job.created_at
    )

@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Streams the generated CSV export directly to the client.
    """
    return await ExportService.generate_csv_stream(session, export_id)
