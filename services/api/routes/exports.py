import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.schema import ExportJob, ExportStatus
from schemas.exports import (
    ExportCreateRequest,
    ExportCreateResponse,
    ExportStatusResponse,
    ExportType,
)
from schemas.auth import TokenData
from services.auth_service import get_current_user
from services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])

@router.post("", response_model=ExportCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    background_tasks: BackgroundTasks,
    body: Optional[ExportCreateRequest] = None,
    session: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Enqueues an asynchronous CSV export for prospects or leads,
    preserving active filters, search query, or selected IDs.
    """
    export_id = str(uuid.uuid4())
    req_data = body.model_dump() if body else {"export_type": "prospects", "scope": "all"}
    export_type_val = req_data.get("export_type") or "prospects"

    job = ExportJob(
        id=export_id,
        user_id=current_user.user_id,
        status=ExportStatus.QUEUED,
        export_type=export_type_val,
        params=req_data,
        progress_percent=0,
        records_processed=0,
        total_records=0
    )
    session.add(job)
    await session.commit()
    
    background_tasks.add_task(ExportService.process_export, export_id)
    return ExportCreateResponse(
        export_id=export_id,
        status=ExportStatus.QUEUED.value,
        message="Export job queued"
    )

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

    # Tenant / user permission verification
    if job.user_id and job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this export"
        )
        
    return ExportStatusResponse(
        id=job.id,
        status=job.status.value,
        export_type=job.export_type or "prospects",
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
    Streams the generated CSV export directly to the client with full security and Excel compatibility.
    """
    return await ExportService.generate_csv_stream(
        session=session,
        export_id=export_id,
        user_id=current_user.user_id
    )
