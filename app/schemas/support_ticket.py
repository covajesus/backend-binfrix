from datetime import datetime

from pydantic import BaseModel, Field


class SupportTicketMessageOut(BaseModel):
    id: str
    author_user_id: str
    author_name: str
    author_role: str
    body: str
    created_at: datetime


class SupportTicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=5000)
    priority: str = "normal"


class SupportTicketMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class SupportTicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None


class SupportTicketOut(BaseModel):
    id: str
    tenant_id: str
    ticket_number: str
    subject: str
    description: str
    status: str
    priority: str
    created_by_user_id: str
    created_by_name: str
    messages: list[SupportTicketMessageOut] = []
    created_at: datetime
    updated_at: datetime
    tenant_name: str | None = None

    model_config = {"from_attributes": True}
