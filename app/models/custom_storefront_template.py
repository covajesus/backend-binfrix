import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CustomStorefrontTemplate(Base):
    """Plantilla de tienda cargada por el tenant (tema + CSS sobre una base built-in)."""

    __tablename__ = "custom_storefront_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_custom_storefront_template_slug"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    slug: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    extends_template: Mapped[str] = mapped_column(String(40), default="sports")
    theme_colors: Mapped[dict] = mapped_column(JSON, default=dict)
    custom_css: Mapped[str] = mapped_column(Text, default="")
    preview_image: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    @property
    def template_id(self) -> str:
        return f"custom-{self.slug}"
