"""FastUI Lead Domain Models.

Active sales pipeline qualification, priority, signal, score, and owner assignment.
"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin


class PipelineStage(str, enum.Enum):
    LEAD = "lead"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class LeadPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class LeadSignal(str, enum.Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


class Lead(Base, TimestampMixin):
    """Active sales pipeline record associated with a master Business."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage, native_enum=False, length=50),
        default=PipelineStage.LEAD,
        nullable=False,
        index=True,
    )
    priority: Mapped[LeadPriority] = mapped_column(
        Enum(LeadPriority, native_enum=False, length=50),
        default=LeadPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    signal: Mapped[LeadSignal] = mapped_column(
        Enum(LeadSignal, native_enum=False, length=50),
        default=LeadSignal.WARM,
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="discover", nullable=False)

    # Relationships
    business = relationship("Business", back_populates="lead_profile")
    owner = relationship("User", back_populates="assigned_leads")
