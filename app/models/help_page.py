import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HelpPage(Base):
    __tablename__ = "help_pages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_help_pages_tenant_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    slug: Mapped[str] = mapped_column(String(80))
    nav_label: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str] = mapped_column(String(255), default="")
    intro: Mapped[str] = mapped_column(Text, default="")
    sections: Mapped[list] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
