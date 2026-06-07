from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.catalog import CatalogProduct
from app.schemas.catalog import CatalogProductCreate, CatalogProductOut, CatalogProductUpdate
from app.utils.catalog import normalize_catalog_payload

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=list[CatalogProductOut])
def list_catalog(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[CatalogProduct]:
    return (
        db.query(CatalogProduct)
        .filter(CatalogProduct.tenant_id == ctx.tenant.id)
        .order_by(CatalogProduct.created_at.desc())
        .all()
    )


@router.post("", response_model=CatalogProductOut, status_code=status.HTTP_201_CREATED)
def create_catalog_item(
    payload: CatalogProductCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CatalogProduct:
    data = normalize_catalog_payload(payload.model_dump())
    item = CatalogProduct(tenant_id=ctx.tenant.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=CatalogProductOut)
def get_catalog_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CatalogProduct:
    item = (
        db.query(CatalogProduct)
        .filter(CatalogProduct.id == item_id, CatalogProduct.tenant_id == ctx.tenant.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return item


@router.patch("/{item_id}", response_model=CatalogProductOut)
def update_catalog_item(
    item_id: str,
    payload: CatalogProductUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CatalogProduct:
    item = (
        db.query(CatalogProduct)
        .filter(CatalogProduct.id == item_id, CatalogProduct.tenant_id == ctx.tenant.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    current = {
        "sku": item.sku,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "product_type": item.product_type,
        "status": item.status,
        "price": item.price,
        "stock": item.stock,
        "images": item.images,
        "color_images": item.color_images,
        "variants": item.variants,
        "variant_mode": item.variant_mode,
    }
    data = normalize_catalog_payload({**current, **payload.model_dump(exclude_unset=True)})

    for field in (
        "sku",
        "title",
        "description",
        "category",
        "product_type",
        "status",
        "price",
        "stock",
        "images",
        "color_images",
        "variants",
        "variant_mode",
    ):
        setattr(item, field, data.get(field))

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_item(
    item_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    item = (
        db.query(CatalogProduct)
        .filter(CatalogProduct.id == item_id, CatalogProduct.tenant_id == ctx.tenant.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(item)
    db.commit()
