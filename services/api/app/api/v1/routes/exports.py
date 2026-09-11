"""FastUI Exports Domain API Routes.

Exposes endpoints for queueing, monitoring, and downloading CSV data exports.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.domains.auth.models import User
from app.domains.exports.schemas import (
    ExportCreateRequest,
    ExportCreateResponse,
    ExportStatusResponse,
)
from app.domains.exports.service import ExportService

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post(
    "",
    response_model=ExportCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue CSV Export",
)
async def create_export(
    background_tasks: BackgroundTasks,
    body: ExportCreateRequest | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportCreateResponse:
    """Enqueues an asynchronous CSV export for prospects, leads, or businesses."""
    res = await ExportService.create_export(
        session=session,
        body=body,
        user=current_user,
    )
    background_tasks.add_task(ExportService.process_export, res.export_id)
    return res


@router.get(
    "/{export_id}",
    response_model=ExportStatusResponse,
    summary="Get Export Status",
)
async def get_export_status(
    export_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportStatusResponse:
    """Checks progress status and download URL of an export job."""
    return await ExportService.get_export_status(
        session=session,
        export_id=export_id,
        user=current_user,
    )


@router.get(
    "/{export_id}/download",
    summary="Download Exported CSV File",
)
async def download_export(
    export_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Streams the generated CSV export with formula injection defense and Excel UTF-8 BOM."""
    return await ExportService.generate_csv_stream(
        session=session,
        export_id=export_id,
        user=current_user,
    )
