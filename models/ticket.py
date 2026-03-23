import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("open", "in_progress", "resolved", "closed", name="ticket_status"),
        default="open",
    )
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="ticket_priority"),
        default="medium",
    )
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(
        Enum("portal", "email", "api", name="ticket_source"),
        default="portal",
    )
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    assignee_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    service_id: Mapped[str | None] = mapped_column(
        ForeignKey("service_catalog.id"), nullable=True
    )
    ai_triage_done: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
