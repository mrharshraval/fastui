import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    """Canonical mixin providing created_at and updated_at timestamps with UTC timezone."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    RETRYING = "retrying"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DiscoveryJob(Base, TimestampMixin):
    __tablename__ = "discovery_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, native_enum=False, length=32), nullable=False)
    query: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    existing_businesses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class DiscoveryTask(Base, TimestampMixin):
    __tablename__ = "discovery_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("discovery_jobs.id"), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, native_enum=False, length=32), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

class WebsiteStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    NO_WEBSITE = "no_website"
    WEBSITE_FOUND = "website_found"

class Business(Base, TimestampMixin):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    business_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    raw_business_name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_business_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    country: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    normalized_phone: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    normalized_website: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    has_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    website_status: Mapped[WebsiteStatus] = mapped_column(
        Enum(WebsiteStatus, native_enum=False, length=32),
        default=WebsiteStatus.UNKNOWN,
        index=True,
        nullable=False,
    )
    qualification_status: Mapped[str] = mapped_column(String, default="unqualified", nullable=False)
    source_platform: Mapped[str] = mapped_column(String, nullable=False)
    last_outreach_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    demos = relationship("ProspectDemo", back_populates="business")
    crawled_websites = relationship("CrawledWebsite", back_populates="business", passive_deletes=True)

class BusinessSource(Base):
    __tablename__ = "business_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    discovery_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_business_source_platform_external_id"),
    )

class ActivityType(str, enum.Enum):
    BUSINESS_DISCOVERED = "business_discovered"
    WEBSITE_VISITED = "website_visited"

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType, native_enum=False, length=32), nullable=False)
    channel: Mapped[str | None] = mapped_column(String, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String, nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

class CrawledWebsite(Base):
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    business = relationship("Business", back_populates="crawled_websites")

class ProspectDemo(Base):
    __tablename__ = "prospect_demos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    template_id: Mapped[str] = mapped_column(String(64), default="dental-default", nullable=False)
    custom_overrides: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    business = relationship("Business", back_populates="demos")
    events = relationship(
        "DemoEvent",
        back_populates="demo",
        cascade="all, delete-orphan",
        order_by="desc(DemoEvent.created_at)",
    )

class DemoEvent(Base):
    __tablename__ = "demo_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    demo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("prospect_demos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    demo = relationship("ProspectDemo", back_populates="events")

