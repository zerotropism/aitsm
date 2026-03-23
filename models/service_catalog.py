import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class ServiceCatalogItem(Base):
    __tablename__ = "service_catalog"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    default_priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="catalog_priority"),
        default="medium",
    )
    form_schema: Mapped[str] = mapped_column(Text, default="[]")  # JSON sérialisé
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
