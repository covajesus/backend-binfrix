from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.seo_page import SeoPage
from app.repositories.base import BaseRepository
from app.schemas.seo_page import (
    SeoCheck,
    SeoPageCreate,
    SeoPageOut,
    SeoPagePublicOut,
    SeoPageUpdate,
    SeoScoreOut,
)
from app.services.base import BaseService


def _normalize_path(path: str) -> str:
    value = (path or "").strip()
    if not value:
        return "/"
    if not value.startswith("/"):
        value = f"/{value}"
    if len(value) > 1 and value.endswith("/"):
        value = value.rstrip("/")
    return value


def score_seo_page(
    *,
    title: str,
    description: str,
    path: str,
    og_title: str,
    og_description: str,
    og_image_url: str,
    focus_keyword: str,
    canonical_path: str,
    all_titles: list[str] | None = None,
    all_descriptions: list[str] | None = None,
    exclude_path: str | None = None,
) -> SeoScoreOut:
    checks: list[SeoCheck] = []
    title_clean = (title or "").strip()
    desc_clean = (description or "").strip()
    keyword = (focus_keyword or "").strip().lower()
    title_len = len(title_clean)
    desc_len = len(desc_clean)

    # Title presence
    if title_clean:
        checks.append(SeoCheck(id="title_present", label="Título presente", status="pass", detail="Hay título definido", weight=10))
    else:
        checks.append(SeoCheck(id="title_present", label="Título presente", status="fail", detail="Falta el título SEO", weight=10))

    # Title length
    if 30 <= title_len <= 60:
        checks.append(SeoCheck(id="title_length", label="Largo del título", status="pass", detail=f"{title_len} caracteres (ideal 30–60)", weight=15))
    elif title_len == 0:
        checks.append(SeoCheck(id="title_length", label="Largo del título", status="fail", detail="Sin título", weight=15))
    elif 20 <= title_len < 30 or 60 < title_len <= 70:
        checks.append(SeoCheck(id="title_length", label="Largo del título", status="warn", detail=f"{title_len} caracteres (ideal 30–60)", weight=15))
    else:
        checks.append(SeoCheck(id="title_length", label="Largo del título", status="fail", detail=f"{title_len} caracteres (ideal 30–60)", weight=15))

    # Description presence
    if desc_clean:
        checks.append(SeoCheck(id="desc_present", label="Meta description presente", status="pass", detail="Hay descripción", weight=10))
    else:
        checks.append(SeoCheck(id="desc_present", label="Meta description presente", status="fail", detail="Falta la meta description", weight=10))

    # Description length
    if 120 <= desc_len <= 160:
        checks.append(SeoCheck(id="desc_length", label="Largo de description", status="pass", detail=f"{desc_len} caracteres (ideal 120–160)", weight=15))
    elif desc_len == 0:
        checks.append(SeoCheck(id="desc_length", label="Largo de description", status="fail", detail="Sin description", weight=15))
    elif 90 <= desc_len < 120 or 160 < desc_len <= 180:
        checks.append(SeoCheck(id="desc_length", label="Largo de description", status="warn", detail=f"{desc_len} caracteres (ideal 120–160)", weight=15))
    else:
        checks.append(SeoCheck(id="desc_length", label="Largo de description", status="fail", detail=f"{desc_len} caracteres (ideal 120–160)", weight=15))

    # Keyword in title
    if keyword:
        if keyword in title_clean.lower():
            checks.append(SeoCheck(id="keyword_title", label="Keyword en título", status="pass", detail=f"“{focus_keyword}” aparece en el título", weight=10))
        else:
            checks.append(SeoCheck(id="keyword_title", label="Keyword en título", status="warn", detail="La keyword no aparece en el título", weight=10))
    else:
        checks.append(SeoCheck(id="keyword_title", label="Keyword en título", status="warn", detail="Define una keyword foco", weight=10))

    # Keyword in description
    if keyword:
        if keyword in desc_clean.lower():
            checks.append(SeoCheck(id="keyword_desc", label="Keyword en description", status="pass", detail="La keyword aparece en la description", weight=5))
        else:
            checks.append(SeoCheck(id="keyword_desc", label="Keyword en description", status="warn", detail="La keyword no aparece en la description", weight=5))
    else:
        checks.append(SeoCheck(id="keyword_desc", label="Keyword en description", status="warn", detail="Sin keyword foco", weight=5))

    # Open Graph
    if (og_title or title_clean).strip():
        checks.append(SeoCheck(id="og_title", label="Open Graph title", status="pass", detail="OG title disponible", weight=5))
    else:
        checks.append(SeoCheck(id="og_title", label="Open Graph title", status="fail", detail="Falta OG title", weight=5))

    if (og_description or desc_clean).strip():
        checks.append(SeoCheck(id="og_desc", label="Open Graph description", status="pass", detail="OG description disponible", weight=5))
    else:
        checks.append(SeoCheck(id="og_desc", label="Open Graph description", status="warn", detail="Falta OG description", weight=5))

    if (og_image_url or "").strip():
        checks.append(SeoCheck(id="og_image", label="Open Graph image", status="pass", detail="Hay imagen social", weight=5))
    else:
        checks.append(SeoCheck(id="og_image", label="Open Graph image", status="warn", detail="Sin imagen OG (recomendado 1200×630)", weight=5))

    # Canonical / path
    path_ok = bool(path) and path.startswith("/") and " " not in path
    if path_ok:
        checks.append(SeoCheck(id="path", label="URL limpia", status="pass", detail=path, weight=5))
    else:
        checks.append(SeoCheck(id="path", label="URL limpia", status="fail", detail="La ruta debe empezar con / y sin espacios", weight=5))

    if (canonical_path or path or "").strip():
        checks.append(SeoCheck(id="canonical", label="Canonical", status="pass", detail="Canonical definido", weight=5))
    else:
        checks.append(SeoCheck(id="canonical", label="Canonical", status="warn", detail="Sin canonical", weight=5))

    # Uniqueness
    titles = [t.strip().lower() for t in (all_titles or []) if t and t.strip()]
    descs = [d.strip().lower() for d in (all_descriptions or []) if d and d.strip()]
    # exclude self counts - caller should pass others only, but we handle duplicates count
    title_dup = titles.count(title_clean.lower()) if title_clean else 0
    desc_dup = descs.count(desc_clean.lower()) if desc_clean else 0
    # If all_titles includes self, duplicate means count > 1
    if title_clean and title_dup <= 1:
        checks.append(SeoCheck(id="unique_title", label="Título único", status="pass", detail="No se repite en otras páginas", weight=5))
    elif title_clean:
        checks.append(SeoCheck(id="unique_title", label="Título único", status="fail", detail="El título se repite en otra página", weight=5))
    else:
        checks.append(SeoCheck(id="unique_title", label="Título único", status="fail", detail="Sin título", weight=5))

    if desc_clean and desc_dup <= 1:
        checks.append(SeoCheck(id="unique_desc", label="Description única", status="pass", detail="No se repite en otras páginas", weight=5))
    elif desc_clean:
        checks.append(SeoCheck(id="unique_desc", label="Description única", status="fail", detail="La description se repite en otra página", weight=5))
    else:
        checks.append(SeoCheck(id="unique_desc", label="Description única", status="fail", detail="Sin description", weight=5))

    earned = 0
    total = 0
    for check in checks:
        total += check.weight
        if check.status == "pass":
            earned += check.weight
        elif check.status == "warn":
            earned += check.weight // 2

    score = int(round((earned / total) * 100)) if total else 0
    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 50:
        grade = "C"
    else:
        grade = "D"

    return SeoScoreOut(score=score, grade=grade, checks=checks)


class SeoPageRepository(BaseRepository[SeoPage]):
    model = SeoPage


class SeoPageService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = SeoPageRepository(db, tenant_id=None)

    def _catalog(self) -> list[SeoPage]:
        return self.db.query(SeoPage).order_by(SeoPage.sort_order, SeoPage.label).all()

    def _to_out(self, row: SeoPage, catalog: list[SeoPage] | None = None) -> SeoPageOut:
        pages = catalog if catalog is not None else self._catalog()
        titles = [p.title for p in pages]
        descriptions = [p.description for p in pages]
        score = score_seo_page(
            title=row.title,
            description=row.description,
            path=row.path,
            og_title=row.og_title,
            og_description=row.og_description,
            og_image_url=row.og_image_url,
            focus_keyword=row.focus_keyword,
            canonical_path=row.canonical_path or row.path,
            all_titles=titles,
            all_descriptions=descriptions,
            exclude_path=row.path,
        )
        return SeoPageOut(
            id=row.id,
            path=row.path,
            label=row.label,
            page_group=row.page_group,
            title=row.title,
            description=row.description,
            og_title=row.og_title,
            og_description=row.og_description,
            og_image_url=row.og_image_url,
            canonical_path=row.canonical_path or row.path,
            robots=row.robots,
            focus_keyword=row.focus_keyword,
            sort_order=row.sort_order,
            is_active=row.is_active,
            score=score,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_public(self, row: SeoPage) -> SeoPagePublicOut:
        return SeoPagePublicOut(
            path=row.path,
            title=row.title,
            description=row.description,
            og_title=row.og_title or row.title,
            og_description=row.og_description or row.description,
            og_image_url=row.og_image_url,
            canonical_path=row.canonical_path or row.path,
            robots=row.robots or "index,follow",
            focus_keyword=row.focus_keyword,
        )

    def list_pages(self) -> list[SeoPageOut]:
        pages = self._catalog()
        return [self._to_out(row, pages) for row in pages]

    def get_by_id(self, page_id: str) -> SeoPageOut:
        row = self.db.query(SeoPage).filter(SeoPage.id == page_id).first()
        if row is None:
            raise NotFoundError("Página SEO no encontrada")
        return self._to_out(row)

    def get_public_by_path(self, path: str) -> SeoPagePublicOut:
        normalized = _normalize_path(path)
        row = (
            self.db.query(SeoPage)
            .filter(SeoPage.path == normalized, SeoPage.is_active.is_(True))
            .first()
        )
        if row is None:
            raise NotFoundError("Página SEO no encontrada")
        return self._to_public(row)

    def create(self, payload: SeoPageCreate) -> SeoPageOut:
        path = _normalize_path(payload.path)
        existing = self.db.query(SeoPage).filter(SeoPage.path == path).first()
        if existing:
            raise ConflictError("Ya existe una página SEO con esa ruta")
        row = SeoPage(
            path=path,
            label=payload.label.strip(),
            page_group=(payload.page_group or "site").strip().lower(),
            title=(payload.title or "").strip(),
            description=(payload.description or "").strip(),
            og_title=(payload.og_title or "").strip(),
            og_description=(payload.og_description or "").strip(),
            og_image_url=(payload.og_image_url or "").strip(),
            canonical_path=_normalize_path(payload.canonical_path or path),
            robots=(payload.robots or "index,follow").strip(),
            focus_keyword=(payload.focus_keyword or "").strip(),
            sort_order=payload.sort_order,
            is_active=payload.is_active,
        )
        self.repo.add(row)
        self.commit()
        return self._to_out(self.repo.refresh(row))

    def update(self, page_id: str, payload: SeoPageUpdate) -> SeoPageOut:
        row = self.db.query(SeoPage).filter(SeoPage.id == page_id).first()
        if row is None:
            raise NotFoundError("Página SEO no encontrada")

        data = payload.model_dump(exclude_unset=True)
        if "path" in data and data["path"] is not None:
            path = _normalize_path(data["path"])
            conflict = (
                self.db.query(SeoPage)
                .filter(SeoPage.path == path, SeoPage.id != page_id)
                .first()
            )
            if conflict:
                raise ConflictError("Ya existe una página SEO con esa ruta")
            data["path"] = path
        if "canonical_path" in data and data["canonical_path"] is not None:
            data["canonical_path"] = _normalize_path(data["canonical_path"] or row.path)
        for field in (
            "label",
            "page_group",
            "title",
            "description",
            "og_title",
            "og_description",
            "og_image_url",
            "robots",
            "focus_keyword",
        ):
            if field in data and data[field] is not None:
                data[field] = str(data[field]).strip()
        if "page_group" in data and data["page_group"] is not None:
            data["page_group"] = data["page_group"].lower()

        for field, value in data.items():
            setattr(row, field, value)

        self.commit()
        return self._to_out(self.repo.refresh(row))

    def delete(self, page_id: str) -> None:
        row = self.db.query(SeoPage).filter(SeoPage.id == page_id).first()
        if row is None:
            raise NotFoundError("Página SEO no encontrada")
        self.repo.delete(row)
        self.commit()
