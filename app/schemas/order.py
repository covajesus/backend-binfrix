from datetime import date

from pydantic import BaseModel, Field


class OrderLineItem(BaseModel):
    id: str | None = None
    product_title: str
    sku: str = ""
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)


class OrderCreate(BaseModel):
    customer_id: str | None = None
    customer_name: str
    customer_email: str = ""
    customer_phone: str = ""
    shipping_address: str = ""
    city: str = ""
    status: str = "pending"
    payment_status: str = "pending"
    items: list[OrderLineItem]
    notes: str = ""


class OrderUpdate(BaseModel):
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    shipping_address: str | None = None
    city: str | None = None
    status: str | None = None
    payment_status: str | None = None
    items: list[OrderLineItem] | None = None
    notes: str | None = None


class OrderOut(BaseModel):
    id: str
    order_number: str
    customer_id: str | None
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    city: str
    status: str
    payment_status: str
    items: list
    total: int
    notes: str
    created_at: date

    model_config = {"from_attributes": True}
