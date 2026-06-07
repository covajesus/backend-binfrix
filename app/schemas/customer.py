from datetime import date

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    phone: str = ""
    city: str = ""
    status: str = "active"
    notes: str = ""


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    city: str | None = None
    status: str | None = None
    notes: str | None = None


class CustomerOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    status: str
    notes: str
    created_at: date

    model_config = {"from_attributes": True}
