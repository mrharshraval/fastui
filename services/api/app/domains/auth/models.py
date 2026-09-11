"""FastUI User and Authentication Domain Models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SALES = "sales"
    VIEWER = "viewer"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=50), default=UserRole.SALES, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verification_otp: Mapped[str | None] = mapped_column(String(32), nullable=True)
    verification_otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    otp_failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    assigned_leads = relationship("Lead", back_populates="owner")
    notes = relationship("Note", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    outreaches = relationship("Outreach", back_populates="user")
    interactions = relationship("Interaction", back_populates="user")
    activities = relationship("Activity", back_populates="user")
    push_subscriptions = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )
