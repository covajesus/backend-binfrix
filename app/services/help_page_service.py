import re

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models.help_page import HelpPage
from app.repositories.base import BaseRepository
from app.schemas.help_page import HelpPageCreate, HelpPageUpdate
from app.services.base import BaseService

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalize_slug(slug: str) -> str:
    return slug.strip().lower()


def _section_value(section, field: str) -> str | list:
    if isinstance(section, dict):
        return section.get(field, "" if field != "paragraphs" and field != "bullets" else [])
    return getattr(section, field, "" if field != "paragraphs" and field != "bullets" else [])


def _serialize_sections(sections: list) -> list[dict]:
    result: list[dict] = []
    for section in sections:
        section_id = str(_section_value(section, "id")).strip()
        title = str(_section_value(section, "title")).strip()
        paragraphs = _section_value(section, "paragraphs") or []
        bullets = _section_value(section, "bullets") or []
        if not section_id or not title:
            continue
        result.append(
            {
                "id": section_id,
                "title": title,
                "paragraphs": [str(p).strip() for p in paragraphs if p and str(p).strip()],
                "bullets": [str(b).strip() for b in bullets if b and str(b).strip()],
            }
        )
    return result


class HelpPageRepository(BaseRepository[HelpPage]):
    model = HelpPage


class HelpPageService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = HelpPageRepository(db, tenant_id=tenant_id)

    def _validate_slug(self, slug: str, exclude_id: str | None = None) -> str:
        normalized = _normalize_slug(slug)
        if not normalized or not _SLUG_RE.match(normalized):
            raise ConflictError("El slug solo puede contener letras minúsculas, números y guiones")
        existing = (
            self.repo._base_query()
            .filter(HelpPage.slug == normalized)
            .first()
        )
        if existing and existing.id != exclude_id:
            raise ConflictError("Ya existe una página de ayuda con ese slug")
        return normalized

    def list_pages(self, active_only: bool = False) -> list[HelpPage]:
        query = self.repo._base_query()
        if active_only:
            query = query.filter(HelpPage.status == "active")
        return query.order_by(HelpPage.sort_order, HelpPage.title).all()

    def get_page(self, page_id: str) -> HelpPage:
        return self.repo.get_by_id(page_id)

    def get_page_by_slug(self, slug: str, active_only: bool = False) -> HelpPage:
        normalized = _normalize_slug(slug)
        query = self.repo._base_query().filter(HelpPage.slug == normalized)
        if active_only:
            query = query.filter(HelpPage.status == "active")
        page = query.first()
        if page is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("Página de ayuda no encontrada")
        return page

    def create_page(self, payload: HelpPageCreate) -> HelpPage:
        slug = self._validate_slug(payload.slug)
        page = HelpPage(
            tenant_id=self.repo.tenant_id,
            slug=slug,
            nav_label=payload.nav_label.strip(),
            title=payload.title.strip(),
            subtitle=payload.subtitle.strip(),
            intro=payload.intro.strip(),
            sections=_serialize_sections(payload.sections),
            sort_order=payload.sort_order,
            status=payload.status,
        )
        self.repo.add(page)
        self.commit()
        return self.repo.refresh(page)

    def update_page(self, page_id: str, payload: HelpPageUpdate) -> HelpPage:
        page = self.repo.get_by_id(page_id)
        data = payload.model_dump(exclude_unset=True)

        if "slug" in data and data["slug"] is not None:
            data["slug"] = self._validate_slug(data["slug"], exclude_id=page_id)
        if "nav_label" in data and data["nav_label"] is not None:
            data["nav_label"] = data["nav_label"].strip()
        if "title" in data and data["title"] is not None:
            data["title"] = data["title"].strip()
        if "subtitle" in data and data["subtitle"] is not None:
            data["subtitle"] = data["subtitle"].strip()
        if "intro" in data and data["intro"] is not None:
            data["intro"] = data["intro"].strip()
        if "sections" in data and data["sections"] is not None:
            data["sections"] = _serialize_sections(data["sections"])

        for field, value in data.items():
            setattr(page, field, value)

        self.commit()
        return self.repo.refresh(page)

    def delete_page(self, page_id: str) -> None:
        page = self.repo.get_by_id(page_id)
        self.repo.delete(page)
        self.commit()
