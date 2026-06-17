from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.license import LicenseCreate, LicenseOut, LicenseUpdate, PlatformProductOut
from app.services.platform_service import LicenseService

router = APIRouter(tags=["licenses"])


def _service(ctx: TenantContext, db: Session) -> LicenseService:
    return LicenseService(db, tenant_id=ctx.tenant.id)


@router.get("/platform-products", response_model=list[PlatformProductOut])
def list_platform_products(db: Session = Depends(get_db)) -> list[PlatformProductOut]:
    return LicenseService(db).list_platform_products()


@router.get("/licenses", response_model=list[LicenseOut])
def list_licenses(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[LicenseOut]:
    return _service(ctx, db).list_licenses()


@router.post("/licenses", response_model=LicenseOut, status_code=status.HTTP_201_CREATED)
def create_license(
    payload: LicenseCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LicenseOut:
    try:
        return _service(ctx, db).create_license(ctx, payload)
    except AppError as exc:
        raise_http(exc)


@router.patch("/licenses/{license_id}", response_model=LicenseOut)
def update_license(
    license_id: str,
    payload: LicenseUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> LicenseOut:
    try:
        return _service(ctx, db).update_license(ctx, license_id, payload)
    except AppError as exc:
        raise_http(exc)
