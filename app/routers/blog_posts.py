from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.schemas.blog_post import BlogPostOut
from app.services.blog_post_service import BlogPostService

router = APIRouter(prefix="/blog-posts", tags=["blog-posts"])


@router.get("", response_model=list[BlogPostOut])
def list_public_blog_posts(db: Session = Depends(get_db)) -> list[BlogPostOut]:
    return BlogPostService(db).list_posts(published_only=True)


@router.get("/{slug}", response_model=BlogPostOut)
def get_public_blog_post(slug: str, db: Session = Depends(get_db)) -> BlogPostOut:
    try:
        return BlogPostService(db).get_by_slug(slug, published_only=True)
    except AppError as exc:
        raise_http(exc)
