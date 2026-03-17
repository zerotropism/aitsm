import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON sérialisé
    status: Mapped[str] = mapped_column(
        Enum("draft", "published", "archived", name="kb_status"),
        default="draft",
    )
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    source_ticket_id: Mapped[str | None] = mapped_column(
        ForeignKey("tickets.id"), nullable=True
    )
    chroma_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
