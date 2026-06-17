from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.dashboard import DashboardOut
from app.services.admin_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard_summary(
    product_id: str = Query(..., description="ID del producto Binfrix seleccionado"),
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> DashboardOut:
    try:
        return DashboardService(db, tenant_id=ctx.tenant.id).get_summary(ctx, product_id)
    except AppError as exc:
        raise_http(exc)
