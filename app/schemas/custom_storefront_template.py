from datetime import datetime

from pydantic import BaseModel, Field


class CustomStorefrontTemplateOut(BaseModel):
    id: str
    slug: str
    template_id: str
    name: str
    description: str
    extends_template: str
    theme_colors: dict[str, str]
    has_custom_css: bool = False
    preview_image: str = ""
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CustomStorefrontTemplatePublicOut(BaseModel):
    template_id: str
    slug: str
    name: str
    description: str
    extends_template: str
    theme_colors: dict[str, str]
    has_custom_css: bool = False
    preview_image: str = ""
