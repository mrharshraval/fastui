"""FastUI Enrichment Domain Models.

Crawled website intelligence, multi-branch practice locations, and extraction cache.
"""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin


class CrawledWebsite(Base, TimestampMixin):
    """Persists comprehensive multi-page website intelligence keyed by normalized domain

    and location signature to support multi-branch practices and corroborated reuse.
    """

    __tablename__ = "crawled_websites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location_signature: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    business_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    canonical_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branches: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    business = relationship("Business", back_populates="crawled_websites", passive_deletes=True)

    __table_args__ = (Index("ix_crawled_websites_domain_loc", "domain", "location_signature"),)
