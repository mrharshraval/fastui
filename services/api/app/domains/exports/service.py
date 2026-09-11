"""FastUI Exports Domain Service.

Chunked streaming CSV exports with formula injection defense and Excel UTF-8 BOM.
"""

import csv
import io
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import SERVICE_DIR
from app.domains.auth.models import User
from app.domains.businesses.models import Business
from app.domains.exports.models import ExportJob, ExportStatus
from app.domains.exports.schemas import (
    ExportCreateRequest,
    ExportCreateResponse,
    ExportStatusResponse,
)
from app.domains.leads.models import Lead, LeadPriority, LeadSignal, PipelineStage
from app.infrastructure.database.session import get_db_session
from app.shared.exceptions import EntityNotFoundError, ForbiddenError

logger = logging.getLogger("fastui.exports")

EXPORT_DIR = SERVICE_DIR / "data" / "exports"


def sanitize_csv_cell(val: Any) -> str:
    """Sanitizes values for CSV output and prevents formula injection."""
    if val is None:
        return ""

    if isinstance(val, bool):
        return "Yes" if val else "No"

    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=UTC)
        return val.strftime("%Y-%m-%d %H:%M:%S UTC")

    if isinstance(val, (int, float)):
        return str(val)

    s = str(val).strip()
    if not s:
        return ""

    # Defend against formula injection in Excel / Sheets
    DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")
    if s.startswith(DANGEROUS_PREFIXES):
        return f"'{s}"

    return s


class ExportService:
    """Manages asynchronous CSV export generation and streaming."""

    PROSPECT_HEADERS = [
        "ID",
        "Business Name",
        "Category",
        "City",
        "State",
        "Country",
        "Address",
        "Phone",
        "Email",
        "Website",
        "Has WhatsApp",
        "Qualification Status",
        "Source",
        "Created At",
    ]

    LEAD_HEADERS = [
        "ID",
        "Business Name",
        "Category",
        "City",
        "State",
        "Country",
        "Address",
        "Phone",
        "Email",
        "Website",
        "Has WhatsApp",
        "Pipeline Stage",
        "Priority",
        "Signal",
        "Score",
        "Owner",
        "Source",
        "Created At",
    ]

    @staticmethod
    def _ensure_export_dir() -> Path:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        return EXPORT_DIR

    @classmethod
    def _format_prospect_row(cls, b: Business) -> list[str]:
        return [
            sanitize_csv_cell(b.id),
            sanitize_csv_cell(b.business_name),
            sanitize_csv_cell(b.category),
            sanitize_csv_cell(b.city),
            sanitize_csv_cell(b.state),
            sanitize_csv_cell(b.country),
            sanitize_csv_cell(b.address),
            sanitize_csv_cell(b.phone),
            sanitize_csv_cell(b.email),
            sanitize_csv_cell(b.website),
            sanitize_csv_cell(b.has_whatsapp),
            sanitize_csv_cell(b.qualification_status),
            sanitize_csv_cell(b.source_platform or "discover"),
            sanitize_csv_cell(b.created_at),
        ]

    @classmethod
    def _format_lead_row(cls, b: Business, l: Lead) -> list[str]:
        stage_str = l.stage.value if hasattr(l.stage, "value") else str(l.stage)
        prio_str = l.priority.value if hasattr(l.priority, "value") else str(l.priority)
        sig_str = l.signal.value if hasattr(l.signal, "value") else str(l.signal)
        return [
            sanitize_csv_cell(b.id),
            sanitize_csv_cell(b.business_name),
            sanitize_csv_cell(b.category),
            sanitize_csv_cell(b.city),
            sanitize_csv_cell(b.state),
            sanitize_csv_cell(b.country),
            sanitize_csv_cell(b.address),
            sanitize_csv_cell(b.phone),
            sanitize_csv_cell(b.email),
            sanitize_csv_cell(b.website),
            sanitize_csv_cell(b.has_whatsapp),
            sanitize_csv_cell(stage_str),
            sanitize_csv_cell(prio_str),
            sanitize_csv_cell(sig_str),
            sanitize_csv_cell(l.score),
            sanitize_csv_cell("me"),
            sanitize_csv_cell(l.source or b.source_platform or "discover"),
            sanitize_csv_cell(l.created_at or b.created_at),
        ]

    @classmethod
    def _build_prospects_query(cls, params: dict[str, Any], user_id: int | None = None) -> Any:
        query = (
            select(Business)
            .outerjoin(Lead, Business.id == Lead.business_id)
            .where(Lead.id.is_(None))
        )

        scope = params.get("scope", "all")
        record_ids = params.get("record_ids")

        if scope == "selected" and record_ids:
            return query.where(Business.id.in_(record_ids)).order_by(
                Business.created_at.desc(), Business.id.desc()
            )

        filters = params.get("filters") or {}

        status_filter = filters.get("qualification_status")
        if status_filter and status_filter.lower() != "all":
            query = query.where(Business.qualification_status == status_filter.lower())

        website_filter = filters.get("website")
        if website_filter == "has_website":
            query = query.where(and_(Business.website.isnot(None), Business.website != ""))
        elif website_filter == "no_website":
            query = query.where(or_(Business.website.is_(None), Business.website == ""))

        source_filter = filters.get("source")
        if source_filter and source_filter.lower() != "all":
            query = query.where(Business.source_platform == source_filter.lower())

        search_query = filters.get("search")
        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    Business.business_name.ilike(term),
                    Business.category.ilike(term),
                    Business.city.ilike(term),
                    Business.state.ilike(term),
                    Business.country.ilike(term),
                    Business.website.ilike(term),
                    Business.phone.ilike(term),
                    Business.email.ilike(term),
                )
            )

        sort_by = filters.get("sort_by", "created_at")
        sort_order = filters.get("sort_order", "desc")
        sort_columns = {
            "created_at": Business.created_at,
            "business_name": Business.business_name,
            "city": Business.city,
            "qualification_status": Business.qualification_status,
        }
        col = sort_columns.get(sort_by, Business.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(col), asc(Business.id))
        else:
            query = query.order_by(desc(col), desc(Business.id))

        return query

    @classmethod
    def _build_leads_query(cls, params: dict[str, Any], user_id: int | None = None) -> Any:
        query = select(Business, Lead).join(Lead, Business.id == Lead.business_id)

        scope = params.get("scope", "all")
        record_ids = params.get("record_ids")

        if scope == "selected" and record_ids:
            return query.where(Business.id.in_(record_ids)).order_by(
                Business.created_at.desc(), Business.id.desc()
            )

        filters = params.get("filters") or {}

        stage_filter = filters.get("stage")
        if stage_filter and stage_filter.lower() != "all":
            for s in PipelineStage:
                if (
                    s.value.lower() == stage_filter.lower()
                    or s.name.lower() == stage_filter.lower()
                ):
                    query = query.where(Lead.stage == s)
                    break

        priority_filter = filters.get("priority")
        if priority_filter and priority_filter.lower() != "all":
            for p in LeadPriority:
                if (
                    p.value.lower() == priority_filter.lower()
                    or p.name.lower() == priority_filter.lower()
                ):
                    query = query.where(Lead.priority == p)
                    break

        signal_filter = filters.get("signal")
        if signal_filter and signal_filter.lower() != "all":
            for sig in LeadSignal:
                if (
                    sig.value.lower() == signal_filter.lower()
                    or sig.name.lower() == signal_filter.lower()
                ):
                    query = query.where(Lead.signal == sig)
                    break

        website_filter = filters.get("website")
        if website_filter == "has_website":
            query = query.where(and_(Business.website.isnot(None), Business.website != ""))
        elif website_filter == "no_website":
            query = query.where(or_(Business.website.is_(None), Business.website == ""))

        source_filter = filters.get("source")
        if source_filter and source_filter.lower() != "all":
            query = query.where(
                or_(
                    Lead.source == source_filter.lower(),
                    Business.source_platform == source_filter.lower(),
                )
            )

        search_query = filters.get("search")
        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    Business.business_name.ilike(term),
                    Business.category.ilike(term),
                    Business.city.ilike(term),
                    Business.state.ilike(term),
                    Business.country.ilike(term),
                    Business.website.ilike(term),
                    Business.phone.ilike(term),
                    Business.email.ilike(term),
                )
            )

        sort_by = filters.get("sort_by", "created_at")
        sort_order = filters.get("sort_order", "desc")
        sort_columns = {
            "created_at": Business.created_at,
            "business_name": Business.business_name,
            "city": Business.city,
        }
        col = sort_columns.get(sort_by, Business.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(col), asc(Business.id))
        else:
            query = query.order_by(desc(col), desc(Business.id))

        return query

    @classmethod
    async def create_export(
        cls,
        session: AsyncSession,
        body: ExportCreateRequest | None,
        user: User,
    ) -> ExportCreateResponse:
        export_id = str(uuid.uuid4())
        req_data = body.model_dump() if body else {"export_type": "prospects", "scope": "all"}
        export_type_val = req_data.get("export_type") or "prospects"

        job = ExportJob(
            id=export_id,
            user_id=user.id,
            status=ExportStatus.QUEUED,
            export_type=export_type_val,
            params=req_data,
            progress_percent=0,
            records_processed=0,
            total_records=0,
        )
        session.add(job)
        await session.commit()

        return ExportCreateResponse(
            export_id=export_id,
            status=ExportStatus.QUEUED.value,
            message="Export job queued",
        )

    @classmethod
    async def get_export_status(
        cls,
        session: AsyncSession,
        export_id: str,
        user: User,
    ) -> ExportStatusResponse:
        job = await session.get(ExportJob, export_id)
        if not job:
            raise EntityNotFoundError("ExportJob", export_id)

        if job.user_id and job.user_id != user.id:
            raise ForbiddenError("Access denied to this export.")

        return ExportStatusResponse(
            id=job.id,
            status=job.status.value,
            export_type=job.export_type or "prospects",
            progress_percent=job.progress_percent,
            records_processed=job.records_processed,
            total_records=job.total_records,
            download_url=job.download_url,
            error_message=job.error_message,
            created_at=job.created_at,
        )

    @classmethod
    async def process_export(cls, export_id: str) -> None:
        export_dir = cls._ensure_export_dir()
        file_path = export_dir / f"{export_id}.csv"

        async with get_db_session() as session:
            job = await session.get(ExportJob, export_id)
            if not job:
                logger.error(f"ExportJob {export_id} not found for execution.")
                return

            try:
                job.status = ExportStatus.PROCESSING
                job.progress_percent = 5
                await session.commit()

                params = job.params or {}
                export_type = job.export_type or "prospects"

                if export_type == "leads":
                    query = cls._build_leads_query(params, job.user_id)
                    headers = cls.LEAD_HEADERS
                else:
                    query = cls._build_prospects_query(params, job.user_id)
                    headers = cls.PROSPECT_HEADERS

                count_query = select(func.count()).select_from(query.subquery())
                total_records = (await session.execute(count_query)).scalar() or 0
                job.total_records = total_records
                await session.commit()

                BATCH_SIZE = 300
                processed = 0

                with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f, lineterminator="\r\n")
                    writer.writerow(headers)

                    if total_records > 0:
                        while processed < total_records:
                            batch_query = query.offset(processed).limit(BATCH_SIZE)
                            res = await session.execute(batch_query)

                            if export_type == "leads":
                                rows = res.all()
                                if not rows:
                                    break
                                for b, l in rows:
                                    writer.writerow(cls._format_lead_row(b, l))
                                processed += len(rows)
                            else:
                                businesses = res.scalars().all()
                                if not businesses:
                                    break
                                for b in businesses:
                                    writer.writerow(cls._format_prospect_row(b))
                                processed += len(businesses)

                            job.records_processed = processed
                            job.progress_percent = min(
                                98, int((processed / total_records) * 95) + 5
                            )
                            await session.commit()

                job.status = ExportStatus.COMPLETED
                job.progress_percent = 100
                job.records_processed = processed
                job.file_path = str(file_path)
                job.download_url = f"/v1/exports/{export_id}/download"
                job.completed_at = datetime.now(UTC)
                await session.commit()
                logger.info(
                    f"ExportJob {export_id} ({export_type}) completed with {processed} records."
                )

            except Exception as e:
                logger.error(f"ExportJob {export_id} failed: {e}", exc_info=True)
                job.status = ExportStatus.FAILED
                job.error_message = str(e)[:500]
                job.completed_at = datetime.now(UTC)
                await session.commit()

    @classmethod
    async def generate_csv_stream(
        cls,
        session: AsyncSession,
        export_id: str,
        user: User,
    ) -> Response:
        job = await session.get(ExportJob, export_id)
        if not job:
            raise EntityNotFoundError("ExportJob", export_id)

        if job.user_id and job.user_id != user.id:
            raise ForbiddenError("Access denied to this export.")

        if job.status != ExportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export is not ready for download (current status: {job.status.value})",
            )

        date_tag = (job.created_at or datetime.now()).strftime("%Y-%m-%d")
        entity_name = job.export_type or "leads"
        filename = f"fastui_{entity_name}_{date_tag}.csv"

        if job.file_path and os.path.exists(job.file_path):
            return FileResponse(
                path=job.file_path,
                media_type="text/csv; charset=utf-8",
                filename=filename,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "no-cache",
                },
            )

        # In-memory fallback
        output = io.StringIO()
        output.write("\ufeff")
        writer = csv.writer(output, lineterminator="\r\n")

        params = job.params or {}
        export_type = job.export_type or "prospects"

        if export_type == "leads":
            query = cls._build_leads_query(params, job.user_id)
            headers = cls.LEAD_HEADERS
            writer.writerow(headers)
            res = await session.execute(query)
            for b, l in res.all():
                writer.writerow(cls._format_lead_row(b, l))
        else:
            query = cls._build_prospects_query(params, job.user_id)
            headers = cls.PROSPECT_HEADERS
            writer.writerow(headers)
            res = await session.execute(query)
            for b in res.scalars().all():
                writer.writerow(cls._format_prospect_row(b))

        return Response(
            content=output.getvalue().encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
