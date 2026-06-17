from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.help_page import HelpPageCreate, HelpPageOut, HelpPageUpdate
from app.services.help_page_service import HelpPageService

router = APIRouter(prefix="/help-pages", tags=["help-pages"])


def _service(ctx: TenantContext, db: Session) -> HelpPageService:
    return HelpPageService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[HelpPageOut])
def list_help_pages(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[HelpPageOut]:
    return _service(ctx, db).list_pages()


@router.post("", response_model=HelpPageOut, status_code=status.HTTP_201_CREATED)
def create_help_page(
    payload: HelpPageCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> HelpPageOut:
    try:
        return _service(ctx, db).create_page(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{page_id}", response_model=HelpPageOut)
def get_help_page(
    page_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> HelpPageOut:
    try:
        return _service(ctx, db).get_page(page_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{page_id}", response_model=HelpPageOut)
def update_help_page(
    page_id: str,
    payload: HelpPageUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> HelpPageOut:
    try:
        return _service(ctx, db).update_page(page_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_help_page(
    page_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_page(page_id)
    except AppError as exc:
        raise_http(exc)
