from datetime import date

from pydantic import BaseModel, Field


class PlatformClientOut(BaseModel):
    id: str
    name: str
    slug: str
    contact: str
    status: str
    licenses_count: int
    created_at: date | None = None


class PlatformClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    principal_name: str = Field(min_length=2, max_length=255)
    principal_email: str = Field(min_length=3, max_length=255)
    principal_password: str = Field(min_length=6, max_length=128)


class PlatformPlanOut(BaseModel):
    id: str
    name: str
    description: str
    max_users: int


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
