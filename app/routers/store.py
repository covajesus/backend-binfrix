"""API pública para el ecommerce frontend (por slug de tenant)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.models.license import TenantLicense
from app.models.order import Order
from app.models.tenant import Tenant
from app.schemas.catalog import CatalogProductOut
from app.schemas.category import CategoryOut
from app.schemas.order import OrderCreate, OrderOut
from app.utils.orders import calc_order_total, generate_order_number, normalize_line_items, today

router = APIRouter(prefix="/store", tags=["store"])


def _get_public_tenant(slug: str, db: Session) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == slug, Tenant.status == "active").first()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")

    license = (
        db.query(TenantLicense)
        .filter(
            TenantLicense.tenant_id == tenant.id,
            TenantLicense.platform_product_id.in_(("ecommerce-b2c", "ecommerce-b2b")),
            TenantLicense.status == "active",
        )
        .first()
    )
    if license is None:
        raise HTTPException(status_code=403, detail="Tienda sin licencia ecommerce activa")

    return tenant


@router.get("/{tenant_slug}/info")
def store_info(tenant_slug: str, db: Session = Depends(get_db)) -> dict:
    tenant = _get_public_tenant(tenant_slug, db)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
    }


@router.get("/{tenant_slug}/categories", response_model=list[CategoryOut])
def store_categories(tenant_slug: str, db: Session = Depends(get_db)) -> list[Category]:
    tenant = _get_public_tenant(tenant_slug, db)
    return (
        db.query(Category)
        .filter(Category.tenant_id == tenant.id, Category.status == "active")
        .order_by(Category.name)
        .all()
    )


@router.get("/{tenant_slug}/catalog", response_model=list[CatalogProductOut])
def store_catalog(tenant_slug: str, db: Session = Depends(get_db)) -> list[CatalogProduct]:
    tenant = _get_public_tenant(tenant_slug, db)
    return (
        db.query(CatalogProduct)
        .filter(CatalogProduct.tenant_id == tenant.id, CatalogProduct.status == "active")
        .order_by(CatalogProduct.title)
        .all()
    )


@router.get("/{tenant_slug}/catalog/{item_id}", response_model=CatalogProductOut)
def store_catalog_item(
    tenant_slug: str,
    item_id: str,
    db: Session = Depends(get_db),
) -> CatalogProduct:
    tenant = _get_public_tenant(tenant_slug, db)
    item = (
        db.query(CatalogProduct)
        .filter(
            CatalogProduct.id == item_id,
            CatalogProduct.tenant_id == tenant.id,
            CatalogProduct.status == "active",
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return item


@router.post("/{tenant_slug}/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def store_create_order(
    tenant_slug: str,
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> Order:
    tenant = _get_public_tenant(tenant_slug, db)
    count = db.query(Order).filter(Order.tenant_id == tenant.id).count()
    items = normalize_line_items([item.model_dump() for item in payload.items])
    order = Order(
        tenant_id=tenant.id,
        order_number=generate_order_number(count),
        customer_id=payload.customer_id,
        customer_name=payload.customer_name.strip(),
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone,
        shipping_address=payload.shipping_address,
        city=payload.city,
        status="pending",
        payment_status="pending",
        items=items,
        total=calc_order_total(items),
        notes=payload.notes,
        created_at=today(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
