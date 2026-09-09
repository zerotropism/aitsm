import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class KBFeedback(Base):
    __tablename__ = "kb_feedback"
    __table_args__ = (UniqueConstraint("article_id", "ticket_id", "user_id", name="uq_feedback"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id: Mapped[str] = mapped_column(
        ForeignKey("kb_articles.id"), nullable=False, index=True
    )
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    vote: Mapped[str] = mapped_column(
        Enum("useful", "not_relevant", name="feedback_vote"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
