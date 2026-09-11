"""FastUI Demos Domain Models.

ProspectDemo generation, token management, and visitor telemetry event recording.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin


class ProspectDemo(Base, TimestampMixin):
    """Personalized interactive website demo link bound to a prospect business."""

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
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    business = relationship("Business", back_populates="demos")
    created_by_user = relationship("User")
    events = relationship(
        "DemoEvent",
        back_populates="demo",
        cascade="all, delete-orphan",
        order_by="desc(DemoEvent.created_at)",
    )


class DemoEvent(Base):
    """Telemetry events tracked when a prospective client views or interacts with their demo."""

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    demo = relationship("ProspectDemo", back_populates="events")
