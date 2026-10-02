from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.schemas.seo_page import SeoPagePublicOut
from app.services.seo_page_service import SeoPageService

router = APIRouter(prefix="/seo-pages", tags=["seo-pages"])


@router.get("", response_model=list[SeoPagePublicOut])
def list_public_seo_pages(db: Session = Depends(get_db)) -> list[SeoPagePublicOut]:
    pages = SeoPageService(db).list_pages()
    return [
        SeoPagePublicOut(
            path=page.path,
            title=page.title,
            description=page.description,
            og_title=page.og_title or page.title,
            og_description=page.og_description or page.description,
            og_image_url=page.og_image_url,
            canonical_path=page.canonical_path or page.path,
            robots=page.robots,
            focus_keyword=page.focus_keyword,
        )
        for page in pages
        if page.is_active
    ]


@router.get("/by-path", response_model=SeoPagePublicOut)
def get_public_seo_page(
    path: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> SeoPagePublicOut:
    try:
        return SeoPageService(db).get_public_by_path(path)
    except AppError as exc:
        raise_http(exc)
