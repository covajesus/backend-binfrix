import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenantLicense(Base):
    __tablename__ = "tenant_licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    platform_product_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("platform_products.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    plan: Mapped[str] = mapped_column(String(50), default="standard")
    starts_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ends_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    max_users: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="licenses")
    platform_product: Mapped["PlatformProduct"] = relationship(back_populates="licenses")
