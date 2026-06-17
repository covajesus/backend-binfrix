from pydantic import BaseModel, Field


class PaymentSessionInitIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)


class PaymentSessionInitOut(BaseModel):
    token: str
    url: str
    order_id: str
    order_number: str
