from datetime import datetime

from pydantic import BaseModel, Field


class CatalogProductCreate(BaseModel):
    sku: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    category: str = ""
    product_type: str = "simple"
    status: str = "active"
    price: int = 0
    stock: int = 0
    images: list[str] = []
    color_images: dict[str, list[str]] = {}
    variants: list[dict] = []
    variant_mode: str | None = None


class CatalogProductUpdate(BaseModel):
    sku: str | None = None
    title: str | None = None
    description: str | None = None
    category: str | None = None
    product_type: str | None = None
    status: str | None = None
    price: int | None = None
    stock: int | None = None
    images: list[str] | None = None
    color_images: dict[str, list[str]] | None = None
    variants: list[dict] | None = None
    variant_mode: str | None = None


class CatalogProductOut(BaseModel):
    id: str
    sku: str
    title: str
    description: str
    category: str
    product_type: str
    status: str
    price: int
    stock: int
    images: list
    color_images: dict
    variants: list
    variant_mode: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
