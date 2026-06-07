import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    payment_number: Mapped[str] = mapped_column(String(30), index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    order_number: Mapped[str] = mapped_column(String(30), default="")
    customer_name: Mapped[str] = mapped_column(String(255), default="")
    amount: Mapped[int] = mapped_column(Integer, default=0)
    method: Mapped[str] = mapped_column(String(30), default="webpay")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    transaction_ref: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    paid_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[date] = mapped_column(Date)
