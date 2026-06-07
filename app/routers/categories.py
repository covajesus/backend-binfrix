from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[Category]:
    return (
        db.query(Category)
        .filter(Category.tenant_id == ctx.tenant.id)
        .order_by(Category.name)
        .all()
    )


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Category:
    category = Category(
        tenant_id=ctx.tenant.id,
        name=payload.name.strip(),
        description=payload.description,
        status=payload.status,
        created_at=date.today(),
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Category:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.tenant_id == ctx.tenant.id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: str,
    payload: CategoryUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Category:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.tenant_id == ctx.tenant.id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    old_name = category.name
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    if payload.name and payload.name != old_name:
        products = (
            db.query(CatalogProduct)
            .filter(
                CatalogProduct.tenant_id == ctx.tenant.id,
                CatalogProduct.category == old_name,
            )
            .all()
        )
        for product in products:
            product.category = payload.name

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.tenant_id == ctx.tenant.id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    count = (
        db.query(CatalogProduct)
        .filter(
            CatalogProduct.tenant_id == ctx.tenant.id,
            CatalogProduct.category == category.name,
        )
        .count()
    )
    if count > 0:
        raise HTTPException(status_code=400, detail="La categoría tiene productos asociados")

    db.delete(category)
    db.commit()
