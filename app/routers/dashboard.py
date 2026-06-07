from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.catalog import CatalogProduct
from app.models.customer import Customer
from app.models.license import TenantLicense
from app.models.platform_product import PlatformProduct
from app.schemas.dashboard import ActivityOut, DashboardOut, StatOut
from app.utils.catalog import get_display_price, get_total_stock, is_variable_product

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _build_ecommerce_dashboard(ctx: TenantContext, db: Session) -> DashboardOut:
    products = (
        db.query(CatalogProduct)
        .filter(CatalogProduct.tenant_id == ctx.tenant.id)
        .all()
    )
    customers = (
        db.query(Customer)
        .filter(Customer.tenant_id == ctx.tenant.id)
        .all()
    )

    active_products = sum(1 for p in products if p.status == "active")
    active_customers = sum(1 for c in customers if c.status == "active")
    without_stock = [p for p in products if get_total_stock(p.__dict__) == 0]
    units = sum(get_total_stock(p.__dict__) for p in products)
    stock_value = 0
    for product in products:
        pdata = product.__dict__
        if is_variable_product(product.product_type):
            for variant in product.variants or []:
                stock_value += int(variant.get("price") or 0) * int(variant.get("stock") or 0)
        else:
            stock_value += int(product.price or 0) * int(product.stock or 0)

    stats = [
        StatOut(
            label="Productos en catálogo",
            value=str(len(products)),
            detail=f"{active_products} activos",
            tone="neutral",
        ),
        StatOut(
            label="Clientes registrados",
            value=str(len(customers)),
            detail=f"{active_customers} activos",
            tone="neutral",
        ),
        StatOut(
            label="Unidades en stock",
            value=f"{units:,}".replace(",", "."),
            detail=f"{len(without_stock)} sin stock" if without_stock else "Inventario disponible",
            tone="warn" if without_stock else "good",
        ),
        StatOut(
            label="Valor del inventario",
            value=f"${stock_value:,}".replace(",", "."),
            detail="Valorización actual",
            tone="good",
        ),
    ]

    activity: list[ActivityOut] = []
    for customer in sorted(customers, key=lambda c: c.created_at, reverse=True)[:2]:
        activity.append(
            ActivityOut(
                title="Cliente registrado",
                subtitle=f"{customer.first_name} {customer.last_name}",
                meta=customer.created_at.strftime("%d-%m-%Y"),
            )
        )
    for product in without_stock[:2]:
        activity.append(
            ActivityOut(
                title="Producto sin stock",
                subtitle=product.title,
                meta=product.sku,
            )
        )

    highlights = [
        f"Catálogo con {len(products)} productos para tu ecommerce.",
        f"Precio desde ${get_display_price(products[0].__dict__):,}".replace(",", ".")
        if products
        else "Agrega productos al catálogo.",
    ]

    return DashboardOut(stats=stats, activity=activity[:5], highlights=highlights[:3])


@router.get("", response_model=DashboardOut)
def dashboard_summary(
    product_id: str = Query(..., description="ID del producto Binfrix seleccionado"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> DashboardOut:
    product = db.get(PlatformProduct, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    if not ctx.user.is_superadmin:
        license_row = (
            db.query(TenantLicense)
            .filter(
                TenantLicense.tenant_id == ctx.tenant.id,
                TenantLicense.platform_product_id == product_id,
                TenantLicense.status == "active",
            )
            .first()
        )
        if license_row is None:
            raise HTTPException(status_code=403, detail="Sin licencia activa para este módulo")

    if product_id in ("ecommerce-b2c", "ecommerce-b2b"):
        return _build_ecommerce_dashboard(ctx, db)

    return DashboardOut(
        stats=[
            StatOut(label="Módulo activo", value=product.name, detail="Licencia vigente", tone="good"),
            StatOut(label="Tenant", value=ctx.tenant.name, detail=ctx.tenant.slug, tone="neutral"),
        ],
        activity=[
            ActivityOut(title="Panel listo", subtitle=product.description[:80], meta="Binfrix"),
        ],
        highlights=[f"Administrando {product.name} para {ctx.tenant.name}."],
    )
