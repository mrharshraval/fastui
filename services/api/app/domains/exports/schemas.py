"""FastUI Exports Domain Schemas & DTOs."""

import enum
from datetime import datetime

from pydantic import BaseModel, Field


class ExportType(str, enum.Enum):
    PROSPECTS = "prospects"
    LEADS = "leads"
    BUSINESSES = "businesses"


class ExportScope(str, enum.Enum):
    SELECTED = "selected"
    FILTERED = "filtered"
    ALL = "all"


class ExportFilterParams(BaseModel):
    search: str | None = None
    qualification_status: str | None = None
    stage: str | None = None
    signal: str | None = None
    priority: str | None = None
    website: str | None = None
    source: str | None = None
    sort_by: str | None = "created_at"
    sort_order: str | None = "desc"


class ExportCreateRequest(BaseModel):
    export_type: ExportType = Field(
        default=ExportType.PROSPECTS, description="Target entity to export"
    )
    scope: ExportScope = Field(
        default=ExportScope.ALL, description="Scope of export: selected, filtered, or all"
    )
    record_ids: list[int] | None = Field(
        default=None, description="List of IDs to export when scope is 'selected'"
    )
    filters: ExportFilterParams | None = Field(
        default=None, description="Active filters to preserve in export"
    )


class ExportCreateResponse(BaseModel):
    export_id: str
    message: str
    status: str = "queued"


class ExportStatusResponse(BaseModel):
    id: str
    status: str
    export_type: str = "prospects"
    progress_percent: int
    records_processed: int
    total_records: int
    download_url: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
