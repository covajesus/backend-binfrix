from pydantic import BaseModel, Field


class PaymentSessionInitIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)
    method: str = ""


class PaymentSandboxCompleteIn(BaseModel):
    token: str = Field(min_length=1, max_length=120)


class PaymentSandboxCompleteOut(BaseModel):
    status: str
    order_number: str


class PagoMovilConfirmIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)
    reference: str = Field(min_length=1, max_length=40)


class PaymentSessionInitOut(BaseModel):
    token: str
    url: str
    order_id: str
    order_number: str
