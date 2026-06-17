from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.catalog import CatalogProductCreate, CatalogProductOut, CatalogProductUpdate
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _service(ctx: TenantContext, db: Session) -> CatalogService:
    return CatalogService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[CatalogProductOut])
def list_catalog(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list:
    return _service(ctx, db).list_products()


@router.post("", response_model=CatalogProductOut, status_code=status.HTTP_201_CREATED)
def create_catalog_item(
    payload: CatalogProductCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CatalogProductOut:
    try:
        return _service(ctx, db).create_product(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{item_id}", response_model=CatalogProductOut)
def get_catalog_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CatalogProductOut:
    try:
        return _service(ctx, db).get_product(item_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{item_id}", response_model=CatalogProductOut)
def update_catalog_item(
    item_id: str,
    payload: CatalogProductUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CatalogProductOut:
    try:
        return _service(ctx, db).update_product(item_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_product(item_id)
    except AppError as exc:
        raise_http(exc)
