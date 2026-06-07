from datetime import date

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    status: str = "active"


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class CategoryOut(BaseModel):
    id: str
    name: str
    description: str
    status: str
    created_at: date

    model_config = {"from_attributes": True}
