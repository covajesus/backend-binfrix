from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TenantSummary
from app.schemas.tenant import TenantCreate, TenantOut, TenantUserCreate, TenantUserOut, TenantUsersPageOut
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _service(db: Session) -> TenantService:
    return TenantService(db)


@router.get("", response_model=list[TenantSummary])
def list_tenants(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TenantSummary]:
    return _service(db).list_for_user(user)


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantOut:
    try:
        return _service(db).create_tenant(payload, user)
    except AppError as exc:
        raise_http(exc)


@router.get("/current", response_model=TenantOut)
def current_tenant(ctx: TenantContext = Depends(get_tenant_context)) -> TenantOut:
    return ctx.tenant


@router.post("/users", response_model=TenantUserOut, status_code=status.HTTP_201_CREATED)
def add_tenant_user(
    payload: TenantUserCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> TenantUserOut:
    try:
        return _service(db).add_tenant_user(ctx, payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/users", response_model=TenantUsersPageOut)
def list_tenant_users(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> TenantUsersPageOut:
    return _service(db).list_tenant_users_page(ctx)
