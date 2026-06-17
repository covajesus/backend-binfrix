from datetime import datetime

from pydantic import BaseModel, Field


class SliderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subtitle: str = ""
    cta: str = "Comprar"
    link_suffix: str = ""
    image_url: str = Field(min_length=1)
    theme: str = "dark"
    sort_order: int = 0
    status: str = "active"


class SliderUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    cta: str | None = None
    link_suffix: str | None = None
    image_url: str | None = None
    theme: str | None = None
    sort_order: int | None = None
    status: str | None = None


class SliderOut(BaseModel):
    id: str
    title: str
    subtitle: str
    cta: str
    link_suffix: str
    image_url: str
    theme: str
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoreSliderOut(BaseModel):
    id: str
    title: str
    subtitle: str
    cta: str
    link_suffix: str
    image_url: str
    theme: str
    sort_order: int

    model_config = {"from_attributes": True}
