from datetime import date

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    order_id: str | None = None
    order_number: str = ""
    customer_name: str = ""
    amount: int = Field(ge=0)
    method: str = "webpay"
    status: str = "pending"
    transaction_ref: str = ""
    paid_at: date | None = None
    notes: str = ""


class PaymentUpdate(BaseModel):
    order_id: str | None = None
    order_number: str | None = None
    customer_name: str | None = None
    amount: int | None = None
    method: str | None = None
    status: str | None = None
    transaction_ref: str | None = None
    paid_at: date | None = None
    notes: str | None = None


class PaymentOut(BaseModel):
    id: str
    payment_number: str
    order_id: str | None
    order_number: str
    customer_name: str
    amount: int
    method: str
    status: str
    transaction_ref: str
    notes: str
    paid_at: date | None
    created_at: date

    model_config = {"from_attributes": True}
