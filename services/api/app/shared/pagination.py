"""FastUI Shared Pagination Primitives & Response Envelopes."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.shared.constants import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, MAX_PAGE_LIMIT

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for offset-based pagination."""

    offset: int = Field(default=DEFAULT_PAGE_OFFSET, ge=0, description="Records to skip")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Max records to return"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination envelope."""

    items: list[T]
    total: int
    offset: int
    limit: int
