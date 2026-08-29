from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExportCreateResponse(BaseModel):
    export_id: str
    message: str

class ExportStatusResponse(BaseModel):
    id: str
    status: str
    progress_percent: int
    records_processed: int
    total_records: int
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
