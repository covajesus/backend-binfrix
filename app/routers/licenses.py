from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.license import TenantLicense
from app.models.platform_product import PlatformProduct
from app.schemas.license import LicenseCreate, LicenseOut, LicenseUpdate, PlatformProductOut

router = APIRouter(tags=["licenses"])


def _license_out(license_row: TenantLicense) -> LicenseOut:
    return LicenseOut(
        id=license_row.id,
        tenant_id=license_row.tenant_id,
        platform_product_id=license_row.platform_product_id,
        platform_product_name=license_row.platform_product.name,
        status=license_row.status,
        plan=license_row.plan,
        starts_at=license_row.starts_at,
        ends_at=license_row.ends_at,
        max_users=license_row.max_users,
        created_at=license_row.created_at,
    )


@router.get("/platform-products", response_model=list[PlatformProductOut])
def list_platform_products(db: Session = Depends(get_db)) -> list[PlatformProduct]:
    return db.query(PlatformProduct).filter(PlatformProduct.is_active.is_(True)).all()


@router.get("/licenses", response_model=list[LicenseOut])
def list_licenses(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[LicenseOut]:
    rows = (
        db.query(TenantLicense)
        .filter(TenantLicense.tenant_id == ctx.tenant.id)
        .order_by(TenantLicense.created_at.desc())
        .all()
    )
    return [_license_out(row) for row in rows]


@router.post("/licenses", response_model=LicenseOut, status_code=status.HTTP_201_CREATED)
def create_license(
    payload: LicenseCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LicenseOut:
    if ctx.role != "admin" and not ctx.user.is_superadmin:
        raise HTTPException(status_code=403, detail="Sin permisos")

    product = db.get(PlatformProduct, payload.platform_product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Producto Binfrix no encontrado")

    existing = (
        db.query(TenantLicense)
        .filter(
            TenantLicense.tenant_id == ctx.tenant.id,
            TenantLicense.platform_product_id == payload.platform_product_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe licencia para este producto")

    license_row = TenantLicense(
        tenant_id=ctx.tenant.id,
        platform_product_id=payload.platform_product_id,
        status=payload.status,
        plan=payload.plan,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        max_users=payload.max_users,
    )
    db.add(license_row)
    db.commit()
    db.refresh(license_row)
    return _license_out(license_row)


@router.patch("/licenses/{license_id}", response_model=LicenseOut)
def update_license(
    license_id: str,
    payload: LicenseUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LicenseOut:
    if ctx.role != "admin" and not ctx.user.is_superadmin:
        raise HTTPException(status_code=403, detail="Sin permisos")

    license_row = (
        db.query(TenantLicense)
        .filter(TenantLicense.id == license_id, TenantLicense.tenant_id == ctx.tenant.id)
        .first()
    )
    if license_row is None:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(license_row, field, value)

    db.commit()
    db.refresh(license_row)
    return _license_out(license_row)
