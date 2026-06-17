from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


def _service(ctx: TenantContext, db: Session) -> CategoryService:
    return CategoryService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[CategoryOut])
def list_categories(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[CategoryOut]:
    return _service(ctx, db).list_categories()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CategoryOut:
    try:
        return _service(ctx, db).create_category(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CategoryOut:
    try:
        return _service(ctx, db).get_category(category_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: str,
    payload: CategoryUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CategoryOut:
    try:
        return _service(ctx, db).update_category(category_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_category(category_id)
    except AppError as exc:
        raise_http(exc)
