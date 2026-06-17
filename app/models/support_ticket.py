import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ticket_number", name="uq_support_tickets_tenant_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    ticket_number: Mapped[str] = mapped_column(String(30), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="open")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    created_by_name: Mapped[str] = mapped_column(String(255), default="")
    messages: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
