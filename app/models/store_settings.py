import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StoreSettings(Base):
    __tablename__ = "store_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_store_settings_tenant"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    phone: Mapped[str] = mapped_column(String(40), default="")
    schedule: Mapped[str] = mapped_column(String(120), default="")
    support_label: Mapped[str] = mapped_column(String(120), default="")
    support_href: Mapped[str] = mapped_column(String(255), default="/help")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    store_url: Mapped[str] = mapped_column(String(500), default="")
    store_logo_url: Mapped[str] = mapped_column(Text, default="")
    storefront_template: Mapped[str] = mapped_column(String(40), default="sports")
    multilingual_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    default_locale: Mapped[str] = mapped_column(String(5), default="es")
    account_label: Mapped[str] = mapped_column(String(120), default="")
    account_href: Mapped[str] = mapped_column(String(255), default="/help")
    promo_messages: Mapped[list] = mapped_column(JSON, default=list)
    header_links: Mapped[list] = mapped_column(JSON, default=list)
    social_links: Mapped[list] = mapped_column(JSON, default=list)
    theme_colors: Mapped[dict] = mapped_column(JSON, default=dict)
    payment_gateway_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_gateway_provider: Mapped[str] = mapped_column(String(40), default="")
    payment_gateway_merchant_id: Mapped[str] = mapped_column(String(40), default="")
    payment_gateway_api_key: Mapped[str] = mapped_column(String(255), default="")
    payment_gateway_environment: Mapped[str] = mapped_column(String(20), default="sandbox")
    billing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    billing_country: Mapped[str] = mapped_column(String(5), default="CL")
    billing_provider: Mapped[str] = mapped_column(String(40), default="")
    billing_api_key: Mapped[str] = mapped_column(String(255), default="")
    billing_username: Mapped[str] = mapped_column(String(255), default="")
    billing_branch: Mapped[str] = mapped_column(String(120), default="Casa Matriz")
    billing_emitter_rut: Mapped[str] = mapped_column(String(20), default="")
    billing_emitter_name: Mapped[str] = mapped_column(String(255), default="")
    billing_emitter_activity: Mapped[str] = mapped_column(String(255), default="")
    billing_emitter_address: Mapped[str] = mapped_column(String(255), default="")
    billing_emitter_commune: Mapped[str] = mapped_column(String(120), default="")
    billing_emitter_city: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
