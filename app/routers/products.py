from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.product import ProductOut
from app.services.platform_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


def _service(ctx: TenantContext, db: Session) -> ProductService:
    return ProductService(db, tenant_id=ctx.tenant.id, user=ctx.user)


@router.get("", response_model=list[ProductOut])
def list_products(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[ProductOut]:
    return _service(ctx, db).list_products()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> ProductOut:
    try:
        return _service(ctx, db).get_product(product_id)
    except AppError as exc:
        raise_http(exc)
