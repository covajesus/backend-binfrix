from pydantic import BaseModel


class ProductOut(BaseModel):
    """Producto SaaS Binfrix (selector del admin)."""

    id: str
    name: str
    description: str
