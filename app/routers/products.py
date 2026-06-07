from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.license import TenantLicense
from app.models.platform_product import PlatformProduct
from app.schemas.product import ProductOut

router = APIRouter(prefix="/products", tags=["products"])


def _licensed_product_ids(ctx: TenantContext, db: Session) -> set[str] | None:
    if ctx.user.is_superadmin:
        return None
    licenses = (
        db.query(TenantLicense)
        .filter(
            TenantLicense.tenant_id == ctx.tenant.id,
            TenantLicense.status == "active",
        )
        .all()
    )
    return {license_row.platform_product_id for license_row in licenses}


@router.get("", response_model=list[ProductOut])
def list_products(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[ProductOut]:
    query = db.query(PlatformProduct).filter(PlatformProduct.is_active.is_(True))
    licensed_ids = _licensed_product_ids(ctx, db)
    products = query.order_by(PlatformProduct.name).all()

    if licensed_ids is not None:
        products = [p for p in products if p.id in licensed_ids]

    return [
        ProductOut(id=p.id, name=p.name, description=p.description)
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> ProductOut:
    product = db.get(PlatformProduct, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    licensed_ids = _licensed_product_ids(ctx, db)
    if licensed_ids is not None and product_id not in licensed_ids:
        raise HTTPException(status_code=403, detail="Sin licencia para este producto")

    return ProductOut(id=product.id, name=product.name, description=product.description)
