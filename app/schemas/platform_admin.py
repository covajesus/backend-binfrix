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
    client_name: str
    product_name: str
    product_id: str
    plan: str
    status: str
    starts_at: date | None = None
    ends_at: date | None = None
