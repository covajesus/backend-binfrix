from datetime import date, datetime

from pydantic import BaseModel, Field


class BlogSection(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str | None = None
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class BlogPostCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    type: str = Field(default="Artículo", max_length=80)
    published_at: date
    read_time: str = Field(default="", max_length=40)
    excerpt: str = ""
    cover_image_url: str = ""
    sections: list[BlogSection] = Field(default_factory=list)
    related_slugs: list[str] = Field(default_factory=list)
    sort_order: int = 0
    status: str = "published"


class BlogPostUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    type: str | None = None
    published_at: date | None = None
    read_time: str | None = None
    excerpt: str | None = None
    cover_image_url: str | None = None
    sections: list[BlogSection] | None = None
    related_slugs: list[str] | None = None
    sort_order: int | None = None
    status: str | None = None


class BlogPostOut(BaseModel):
    id: str
    slug: str
    title: str
    type: str
    published_at: date
    read_time: str
    excerpt: str
    cover_image_url: str = ""
    sections: list[BlogSection]
    related_slugs: list[str]
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
