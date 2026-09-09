import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Change(Base):
    __tablename__ = "changes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("draft", "review", "approved", "rejected", "done", name="change_status"),
        default="draft",
    )
    risk: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="change_risk"),
        default="medium",
    )
    planned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    approver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
