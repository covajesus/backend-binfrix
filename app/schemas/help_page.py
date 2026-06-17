from datetime import datetime

from pydantic import BaseModel, Field


class HelpSection(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class HelpPageCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    nav_label: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    subtitle: str = ""
    intro: str = ""
    sections: list[HelpSection] = Field(default_factory=list)
    sort_order: int = 0
    status: str = "active"


class HelpPageUpdate(BaseModel):
    slug: str | None = None
    nav_label: str | None = None
    title: str | None = None
    subtitle: str | None = None
    intro: str | None = None
    sections: list[HelpSection] | None = None
    sort_order: int | None = None
    status: str | None = None


class HelpPageOut(BaseModel):
    id: str
    slug: str
    nav_label: str
    title: str
    subtitle: str
    intro: str
    sections: list[HelpSection]
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
