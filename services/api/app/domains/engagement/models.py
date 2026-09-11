"""FastUI Engagement Domain Models.

CRM touchpoints, notes, tasks, reminders, outreaches, interactions, and chronological activity audit stream.
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
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutreachChannel(str, enum.Enum):
    CALL = "call"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class OutreachStatus(str, enum.Enum):
    INITIATED = "initiated"
    CONNECTED = "connected"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    SENT = "sent"
    DELIVERED = "delivered"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


class InteractionType(str, enum.Enum):
    CALL_CONVERSATION = "call_conversation"
    WHATSAPP_CHAT = "whatsapp_chat"
    EMAIL_THREAD = "email_thread"
    MEETING = "meeting"
    DEMO = "demo"


class ActivityType(str, enum.Enum):
    BUSINESS_DISCOVERED = "business_discovered"
    LEAD_CREATED = "lead_created"
    WEBSITE_VISITED = "website_visited"
    CALL_INITIATED = "call_initiated"
    WHATSAPP_OPENED = "whatsapp_opened"
    EMAIL_INITIATED = "email_initiated"
    INTERACTION_LOGGED = "interaction_logged"
    NOTE_ADDED = "note_added"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    REMINDER_CREATED = "reminder_created"
    REMINDER_COMPLETED = "reminder_completed"
    STATUS_CHANGED = "status_changed"
    PROPOSAL_SENT = "proposal_sent"


class Contact(Base, TimestampMixin):
    """Person or stakeholder associated with a Business."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_phone: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    business = relationship("Business", back_populates="contacts")
    notes = relationship("Note", back_populates="contact")
    tasks = relationship("Task", back_populates="contact")
    reminders = relationship("Reminder", back_populates="contact")
    outreaches = relationship("Outreach", back_populates="contact")
    interactions = relationship("Interaction", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")


class Note(Base, TimestampMixin):
    """Freeform rich-text note recorded by an account representative."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    business = relationship("Business", back_populates="notes")
    contact = relationship("Contact", back_populates="notes")
    user = relationship("User", back_populates="notes")


class Task(Base, TimestampMixin):
    """Actionable to-do work item assigned to a sales representative."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=50),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="tasks")
    contact = relationship("Contact", back_populates="tasks")
    user = relationship("User", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task")


class Reminder(Base, TimestampMixin):
    """Scheduled time-based push/email alert trigger."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, native_enum=False, length=50),
        default=ReminderStatus.PENDING,
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    business = relationship("Business", back_populates="reminders")
    contact = relationship("Contact", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
    task = relationship("Task", back_populates="reminders")


class Outreach(Base, TimestampMixin):
    """Outbound contact attempt made by a user via call, WhatsApp, or email."""

    __tablename__ = "outreaches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    channel: Mapped[OutreachChannel] = mapped_column(
        Enum(OutreachChannel, native_enum=False, length=50), nullable=False, index=True
    )
    status: Mapped[OutreachStatus] = mapped_column(
        Enum(OutreachStatus, native_enum=False, length=50),
        default=OutreachStatus.INITIATED,
        nullable=False,
        index=True,
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    business = relationship("Business", back_populates="outreaches")
    contact = relationship("Contact", back_populates="outreaches")
    user = relationship("User", back_populates="outreaches")
    interactions = relationship("Interaction", back_populates="outreach")


class Interaction(Base, TimestampMixin):
    """Two-way completed engagement with logged outcome and sentiment."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    outreach_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("outreaches.id", ondelete="SET NULL"), nullable=True, index=True
    )

    type: Mapped[InteractionType] = mapped_column(
        Enum(InteractionType, native_enum=False, length=50), nullable=False, index=True
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(50), default="neutral", nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    business = relationship("Business", back_populates="interactions")
    contact = relationship("Contact", back_populates="interactions")
    user = relationship("User", back_populates="interactions")
    outreach = relationship("Outreach", back_populates="interactions")


class Activity(Base):
    """Chronological audit trail event logging all touchpoints and state transitions."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, native_enum=False, length=50), nullable=False, index=True
    )
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    business = relationship("Business", back_populates="activities")
    user = relationship("User", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")
