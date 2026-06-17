from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, serialize_user_out
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.tenant import TenantMembership
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, MessageResponse, TenantSummary, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_role(user: User, tenant_id: str | None, db: Session) -> str:
    if user.is_superadmin:
        return "admin"
    if not tenant_id:
        return "staff"
    membership = (
        db.query(TenantMembership)
        .filter(TenantMembership.user_id == user.id, TenantMembership.tenant_id == tenant_id)
        .first()
    )
    return membership.role if membership else "staff"


def _user_tenants(user: User, db: Session) -> list[TenantSummary]:
    if user.is_superadmin:
        from app.models.tenant import Tenant

        return [
            TenantSummary(id=t.id, name=t.name, slug=t.slug, role="admin")
            for t in db.query(Tenant).order_by(Tenant.name).all()
        ]

    memberships = (
        db.query(TenantMembership)
        .options(joinedload(TenantMembership.tenant))
        .filter(TenantMembership.user_id == user.id)
        .all()
    )
    result = []
    for membership in memberships:
        tenant = membership.tenant
        result.append(
            TenantSummary(id=tenant.id, name=tenant.name, slug=tenant.slug, role=membership.role)
        )
    return result


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.email == payload.email)
        .first()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_access_token(user.id, user.email)
    tenants = _user_tenants(user, db)

    return LoginResponse(
        token=token,
        user=serialize_user_out(user),
        tenants=tenants,
    )


@router.get("/me", response_model=UserOut)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    user = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).first()
    return serialize_user_out(user)


@router.post("/logout", response_model=MessageResponse)
def logout() -> MessageResponse:
    return MessageResponse(message="Sesión cerrada")
