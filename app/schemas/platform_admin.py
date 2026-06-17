from datetime import date

from pydantic import BaseModel


class PlatformClientOut(BaseModel):
    id: str
    name: str
    slug: str
    contact: str
    status: str
    licenses_count: int
    created_at: date | None = None


class PlatformLicenseOut(BaseModel):
    id: str
    tenant_id: str
    client_name: str
    product_name: str
    product_id: str
    plan: str
    status: str
    starts_at: date | None = None
    ends_at: date | None = None
    max_users: int | None = None


class PlatformLicenseCreate(BaseModel):
    tenant_id: str
    platform_product_id: str
    plan: str = "standard"
    status: str = "active"
    starts_at: date | None = None
    ends_at: date | None = None
    max_users: int | None = None


class PlatformLicenseUpdate(BaseModel):
    plan: str | None = None
    status: str | None = None
    starts_at: date | None = None
    ends_at: date | None = None
    max_users: int | None = None
