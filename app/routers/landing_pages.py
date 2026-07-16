from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.landing_page import LandingPageCreate, LandingPageOut, LandingPageUpdate
from app.services.landing_page_service import LandingPageService

router = APIRouter(prefix="/landing-pages", tags=["landing-pages"])


def _service(ctx: TenantContext, db: Session) -> LandingPageService:
    return LandingPageService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[LandingPageOut])
def list_landing_pages(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[LandingPageOut]:
    return _service(ctx, db).list_pages()


@router.post("", response_model=LandingPageOut, status_code=status.HTTP_201_CREATED)
def create_landing_page(
    payload: LandingPageCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LandingPageOut:
    try:
        return _service(ctx, db).create_page(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{page_id}", response_model=LandingPageOut)
def get_landing_page(
    page_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LandingPageOut:
    try:
        return _service(ctx, db).get_page(page_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{page_id}", response_model=LandingPageOut)
def update_landing_page(
    page_id: str,
    payload: LandingPageUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LandingPageOut:
    try:
        return _service(ctx, db).update_page(page_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_landing_page(
    page_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_page(page_id)
    except AppError as exc:
        raise_http(exc)
