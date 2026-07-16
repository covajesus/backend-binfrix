import re
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models.blog_post import BlogPost
from app.repositories.base import BaseRepository
from app.schemas.blog_post import BlogPostCreate, BlogPostOut, BlogPostUpdate
from app.services.base import BaseService

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_STATUSES = {"draft", "published"}


def _normalize_slug(slug: str) -> str:
    return slug.strip().lower()


def _section_value(section, field: str):
    if isinstance(section, dict):
        return section.get(field)
    return getattr(section, field, None)


def _serialize_sections(sections: list) -> list[dict]:
    result: list[dict] = []
    for section in sections:
        section_id = str(_section_value(section, "id") or "").strip()
        if not section_id:
            continue
        raw_title = _section_value(section, "title")
        title = str(raw_title).strip() if raw_title else None
        paragraphs = _section_value(section, "paragraphs") or []
        bullets = _section_value(section, "bullets") or []
        clean_paragraphs = [str(p).strip() for p in paragraphs if p and str(p).strip()]
        clean_bullets = [str(b).strip() for b in bullets if b and str(b).strip()]
        if not title and not clean_paragraphs and not clean_bullets:
            continue
        entry: dict = {
            "id": section_id,
            "paragraphs": clean_paragraphs,
            "bullets": clean_bullets,
        }
        if title:
            entry["title"] = title
        result.append(entry)
    return result


def _serialize_related_slugs(slugs: list) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for slug in slugs or []:
        normalized = _normalize_slug(str(slug))
        if not normalized or normalized in seen:
            continue
        if not _SLUG_RE.match(normalized):
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


class BlogPostRepository(BaseRepository[BlogPost]):
    model = BlogPost


class BlogPostService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = BlogPostRepository(db, tenant_id=None)

    def _to_out(self, row: BlogPost) -> BlogPostOut:
        return BlogPostOut.model_validate(row)

    def _validate_slug(self, slug: str, exclude_id: str | None = None) -> str:
        normalized = _normalize_slug(slug)
        if not normalized or not _SLUG_RE.match(normalized):
            raise ConflictError("El slug solo puede contener letras minúsculas, números y guiones")
        existing = self.db.query(BlogPost).filter(BlogPost.slug == normalized).first()
        if existing and existing.id != exclude_id:
            raise ConflictError("Ya existe un artículo con ese slug")
        return normalized

    def _validate_status(self, status: str) -> str:
        normalized = status.strip().lower()
        if normalized not in VALID_STATUSES:
            raise AppError("Estado no válido (draft o published)")
        return normalized

    def list_posts(self, published_only: bool = False) -> list[BlogPostOut]:
        query = self.db.query(BlogPost)
        if published_only:
            query = query.filter(BlogPost.status == "published")
        rows = query.order_by(BlogPost.sort_order, BlogPost.published_at.desc()).all()
        return [self._to_out(row) for row in rows]

    def get_by_id(self, post_id: str) -> BlogPostOut:
        row = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if row is None:
            raise NotFoundError("Artículo no encontrado")
        return self._to_out(row)

    def get_by_slug(self, slug: str, published_only: bool = False) -> BlogPostOut:
        normalized = _normalize_slug(slug)
        query = self.db.query(BlogPost).filter(BlogPost.slug == normalized)
        if published_only:
            query = query.filter(BlogPost.status == "published")
        row = query.first()
        if row is None:
            raise NotFoundError("Artículo no encontrado")
        return self._to_out(row)

    def create(self, payload: BlogPostCreate) -> BlogPostOut:
        slug = self._validate_slug(payload.slug)
        status = self._validate_status(payload.status)
        row = BlogPost(
            slug=slug,
            title=payload.title.strip(),
            type=(payload.type or "Artículo").strip() or "Artículo",
            published_at=payload.published_at or date.today(),
            read_time=(payload.read_time or "").strip(),
            excerpt=(payload.excerpt or "").strip(),
            sections=_serialize_sections(payload.sections),
            related_slugs=_serialize_related_slugs(payload.related_slugs),
            sort_order=payload.sort_order,
            status=status,
        )
        self.repo.add(row)
        self.commit()
        return self._to_out(self.repo.refresh(row))

    def update(self, post_id: str, payload: BlogPostUpdate) -> BlogPostOut:
        row = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if row is None:
            raise NotFoundError("Artículo no encontrado")

        data = payload.model_dump(exclude_unset=True)

        if "slug" in data and data["slug"] is not None:
            data["slug"] = self._validate_slug(data["slug"], exclude_id=post_id)
        if "status" in data and data["status"] is not None:
            data["status"] = self._validate_status(data["status"])
        if "title" in data and data["title"] is not None:
            data["title"] = data["title"].strip()
        if "type" in data and data["type"] is not None:
            data["type"] = data["type"].strip() or "Artículo"
        if "read_time" in data and data["read_time"] is not None:
            data["read_time"] = data["read_time"].strip()
        if "excerpt" in data and data["excerpt"] is not None:
            data["excerpt"] = data["excerpt"].strip()
        if "sections" in data and data["sections"] is not None:
            data["sections"] = _serialize_sections(data["sections"])
        if "related_slugs" in data and data["related_slugs"] is not None:
            data["related_slugs"] = _serialize_related_slugs(data["related_slugs"])

        for field, value in data.items():
            setattr(row, field, value)

        self.commit()
        return self._to_out(self.repo.refresh(row))

    def delete(self, post_id: str) -> None:
        row = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if row is None:
            raise NotFoundError("Artículo no encontrado")
        self.repo.delete(row)
        self.commit()
