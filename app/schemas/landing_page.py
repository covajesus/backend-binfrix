from datetime import datetime

from pydantic import BaseModel, Field


class LandingSection(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class LandingPageCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    campaign_name: str = ""
    title: str = Field(min_length=1, max_length=255)
    subtitle: str = ""
    intro: str = ""
    hero_image_url: str = ""
    hero_cta_label: str = ""
    hero_cta_href: str = ""
    sections: list[LandingSection] = Field(default_factory=list)
    sort_order: int = 0
    status: str = "draft"


class LandingPageUpdate(BaseModel):
    slug: str | None = None
    campaign_name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    intro: str | None = None
    hero_image_url: str | None = None
    hero_cta_label: str | None = None
    hero_cta_href: str | None = None
    sections: list[LandingSection] | None = None
    sort_order: int | None = None
    status: str | None = None


class LandingPageOut(BaseModel):
    id: str
    slug: str
    campaign_name: str
    title: str
    subtitle: str
    intro: str
    hero_image_url: str
    hero_cta_label: str
    hero_cta_href: str
    sections: list[LandingSection]
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
