from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=8, max_length=50)
    email: EmailStr
    interest: str = Field(min_length=1, max_length=255)


class ContactMessageUpdate(BaseModel):
    status: str | None = None


class ContactMessageOut(BaseModel):
    id: str
    name: str
    phone: str
    email: EmailStr
    interest: str
    status: str
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}
