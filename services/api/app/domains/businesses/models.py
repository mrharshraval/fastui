"""FastUI Business Domain Models.

Authoritative master company records and multi-source scraping provenance.
"""

import enum
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin


class WebsiteStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    WEBSITE_FOUND = "website_found"
    NO_WEBSITE = "no_website"


class Business(Base, TimestampMixin):
    """Authoritative master company entity."""

    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    canonical_name: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    business_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    raw_business_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalized_business_name: Mapped[str | None] = mapped_column(
        String(255), index=True, nullable=True
    )
    category: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)

    # Normalization & Deduplication signals
    normalized_phone: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    normalized_website: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)

    # Location & Contact Information
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    has_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    website_status: Mapped[WebsiteStatus] = mapped_column(
        Enum(WebsiteStatus, native_enum=False, length=50),
        default=WebsiteStatus.UNKNOWN,
        index=True,
        nullable=False,
    )

    # Contact tracking & Prospect Qualification
    source_platform: Mapped[str | None] = mapped_column(
        String(100), default="discover", nullable=True
    )
    qualification_status: Mapped[str] = mapped_column(
        String(50), default="unqualified", index=True, nullable=False
    )
    last_outreach_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    lead_profile = relationship(
        "Lead",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    contacts = relationship(
        "Contact", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    sources = relationship(
        "BusinessSource",
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notes = relationship(
        "Note", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    tasks = relationship(
        "Task", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    reminders = relationship(
        "Reminder", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    outreaches = relationship(
        "Outreach", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    interactions = relationship(
        "Interaction", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    activities = relationship(
        "Activity", back_populates="business", cascade="all, delete-orphan", passive_deletes=True
    )
    demos = relationship(
        "ProspectDemo",
        back_populates="business",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    crawled_websites = relationship(
        "CrawledWebsite", back_populates="business", passive_deletes=True
    )


class BusinessSource(Base):
    """Multi-source provenance tracking for discovered businesses."""

    __tablename__ = "business_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discovery_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("discovery_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    platform: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_business_source_platform_external_id"),
        Index("ix_business_sources_business_platform", "business_id", "platform"),
    )

    business = relationship("Business", back_populates="sources")
    discovery_job = relationship("DiscoveryJob", back_populates="sources")
