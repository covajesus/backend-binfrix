from datetime import datetime

from pydantic import BaseModel, Field


class SeoCheck(BaseModel):
    id: str
    label: str
    status: str  # pass | warn | fail
    detail: str
    weight: int = 0


class SeoScoreOut(BaseModel):
    score: int
    grade: str
    checks: list[SeoCheck]


class SeoPageCreate(BaseModel):
    path: str = Field(min_length=1, max_length=255)
    label: str = Field(min_length=1, max_length=255)
    page_group: str = Field(default="site", max_length=40)
    title: str = ""
    description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image_url: str = ""
    canonical_path: str = ""
    robots: str = "index,follow"
    focus_keyword: str = ""
    sort_order: int = 0
    is_active: bool = True


class SeoPageUpdate(BaseModel):
    path: str | None = None
    label: str | None = None
    page_group: str | None = None
    title: str | None = None
    description: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image_url: str | None = None
    canonical_path: str | None = None
    robots: str | None = None
    focus_keyword: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class SeoPageOut(BaseModel):
    id: str
    path: str
    label: str
    page_group: str
    title: str
    description: str
    og_title: str
    og_description: str
    og_image_url: str
    canonical_path: str
    robots: str
    focus_keyword: str
    sort_order: int
    is_active: bool
    score: SeoScoreOut
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SeoPagePublicOut(BaseModel):
    path: str
    title: str
    description: str
    og_title: str
    og_description: str
    og_image_url: str
    canonical_path: str
    robots: str
    focus_keyword: str = ""
