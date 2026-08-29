from typing import Optional
from pydantic import BaseModel, Field

class DiscoverySearchParams(BaseModel):
    """Normalized search query parameters passed to source adapters."""
    target_audience: str = Field(..., description="Target business profession/category, e.g. 'Dentist'")
    location: str = Field(..., description="Target geographical location, e.g. 'Ahmedabad, Gujarat, India'")
    limit: int = Field(default=20, ge=1, le=100, description="Max leads to fetch")

class DiscoveredLead(BaseModel):
    """Contract for a raw lead discovered by any scraping source adapter."""
    name: str = Field(..., min_length=1)
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    source_platform: str = Field(default="google_maps")
    source_url: Optional[str] = None
