import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SeoPage(Base):
    __tablename__ = "seo_pages"
    __table_args__ = (UniqueConstraint("path", name="uq_seo_pages_path"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    path: Mapped[str] = mapped_column(String(255), index=True)
    label: Mapped[str] = mapped_column(String(255))
    page_group: Mapped[str] = mapped_column(String(40), default="site")
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    og_title: Mapped[str] = mapped_column(String(255), default="")
    og_description: Mapped[str] = mapped_column(Text, default="")
    og_image_url: Mapped[str] = mapped_column(Text, default="")
    canonical_path: Mapped[str] = mapped_column(String(255), default="")
    robots: Mapped[str] = mapped_column(String(80), default="index,follow")
    focus_keyword: Mapped[str] = mapped_column(String(120), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
