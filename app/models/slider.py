import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Slider(Base):
    __tablename__ = "sliders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str] = mapped_column(String(255), default="")
    cta: Mapped[str] = mapped_column(String(120), default="Comprar")
    link_suffix: Mapped[str] = mapped_column(String(255), default="")
    image_url: Mapped[str] = mapped_column(Text)
    theme: Mapped[str] = mapped_column(String(10), default="dark")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
