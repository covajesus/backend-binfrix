from datetime import date, datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantUserCreate(BaseModel):
    email: str
    name: str
    password: str = Field(min_length=6)
    role: str = "staff"


class TenantUserOut(BaseModel):
    id: str
    user_id: str
    email: str
    name: str
    role: str
    is_principal: bool = False

    model_config = {"from_attributes": True}


class TenantUsersPageOut(BaseModel):
    max_users: int
    current_users: int
    can_invite: bool
    users: list[TenantUserOut]
