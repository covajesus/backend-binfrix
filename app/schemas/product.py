from datetime import date

from pydantic import BaseModel


class ProductOut(BaseModel):
    """Producto SaaS Binfrix (selector del admin)."""

    id: str
    name: str
    description: str
    licensed: bool = False
    license_plan: str | None = None
    license_max_users: int | None = None
    license_starts_at: date | None = None
    license_ends_at: date | None = None
