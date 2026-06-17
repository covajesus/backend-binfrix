from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.store_settings import StoreSettingsOut, StoreSettingsUpdate
from app.services.store_settings_service import StoreSettingsService

router = APIRouter(prefix="/store-settings", tags=["store-settings"])


def _service(ctx: TenantContext, db: Session) -> StoreSettingsService:
    return StoreSettingsService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=StoreSettingsOut)
def get_store_settings(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> StoreSettingsOut:
    try:
        return _service(ctx, db).get_settings()
    except AppError as exc:
        raise_http(exc)


@router.patch("", response_model=StoreSettingsOut)
def update_store_settings(
    payload: StoreSettingsUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> StoreSettingsOut:
    try:
        return _service(ctx, db).update_settings(payload)
    except AppError as exc:
        raise_http(exc)
