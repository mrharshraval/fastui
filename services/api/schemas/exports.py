from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ExportType(str, Enum):
    PROSPECTS = "prospects"
    LEADS = "leads"
    BUSINESSES = "businesses"

class ExportScope(str, Enum):
    SELECTED = "selected"
    FILTERED = "filtered"
    ALL = "all"

class ExportFilterParams(BaseModel):
    search: Optional[str] = None
    qualification_status: Optional[str] = None
    stage: Optional[str] = None
    signal: Optional[str] = None
    priority: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"

class ExportCreateRequest(BaseModel):
    export_type: ExportType = Field(default=ExportType.PROSPECTS, description="Target entity to export")
    scope: ExportScope = Field(default=ExportScope.ALL, description="Scope of export: selected, filtered, or all")
    record_ids: Optional[List[int]] = Field(default=None, description="List of IDs to export when scope is 'selected'")
    filters: Optional[ExportFilterParams] = Field(default=None, description="Active filters to preserve in export")

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
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
