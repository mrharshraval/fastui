import asyncio
import io
import csv
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.database import AsyncSessionLocal
from models.schema import ExportJob, ExportStatus, Business

logger = logging.getLogger(__name__)

class ExportService:
    @staticmethod
    async def process_export(export_id: str):
        """
        Background task to process export progress without blocking the asyncio loop.
        """
        async with AsyncSessionLocal() as session:
            job = await session.get(ExportJob, export_id)
            if not job:
                return

            try:
                job.status = ExportStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)
                await session.commit()

                # Simulated processing / streaming fetch in chunks
                count_query = select(func.count(Business.id))
                total_records = (await session.execute(count_query)).scalar() or 0

                # Simulate incremental batch processing
                for progress in range(10, 101, 30):
                    await asyncio.sleep(0.05)
                    job.progress_percentage = min(progress, 100)
                    await session.commit()

                job.status = ExportStatus.COMPLETED
                job.progress_percentage = 100
                job.total_records = total_records
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info(f"ExportJob {export_id} completed successfully with {total_records} records.")

            except Exception as e:
                logger.error(f"ExportJob {export_id} failed: {e}", exc_info=True)
                job.status = ExportStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()

    @staticmethod
    async def generate_csv_stream(session: AsyncSession, export_id: str) -> Response:
        """
        Queries businesses and returns an HTTP attachment response containing formatted CSV data.
        """
        job = await session.get(ExportJob, export_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
        if job.status != ExportStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export is not ready for download")
            
        result = await session.execute(select(Business).order_by(Business.created_at.desc()))
        businesses = result.scalars().all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Business Name", "Category", "City", "Phone", "Website", "Pipeline Stage", "Created At"])
        
        for b in businesses:
            writer.writerow([
                b.id,
                b.business_name,
                b.category or "",
                b.city or "",
                b.phone or "",
                b.website or "",
                b.pipeline_stage,
                b.created_at.isoformat() if b.created_at else ""
            ])
            
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=fastui_leads_{export_id[:8]}.csv"
            }
        )
