from datetime import date, datetime

from pydantic import BaseModel


class LicenseCreate(BaseModel):
    platform_product_id: str
    plan: str = "standard"
    status: str = "active"
    starts_at: date | None = None
    ends_at: date | None = None
    max_users: int | None = None


class LicenseUpdate(BaseModel):
    plan: str | None = None
    status: str | None = None
    starts_at: date | None = None
    ends_at: date | None = None
    max_users: int | None = None


class PlatformProductOut(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool

    model_config = {"from_attributes": True}


class LicenseOut(BaseModel):
    id: str
    tenant_id: str
    platform_product_id: str
    platform_product_name: str
    status: str
    plan: str
    starts_at: date | None
    ends_at: date | None
    max_users: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
