from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.core.roles import ROLE_ADMIN, is_platform_admin
from app.core.security import decode_access_token
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.schemas.auth import UserOut

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, payload["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_platform_role_slug(user: User) -> str:
    if user.role:
        return user.role.slug
    if user.is_superadmin:
        return ROLE_ADMIN
    return "staff"


def serialize_user_out(user: User) -> UserOut:
    role_slug = get_platform_role_slug(user)
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=role_slug,
        role_name=user.role.name if user.role else "",
        is_superadmin=user.is_superadmin,
    )


def get_current_user_out(user: User = Depends(get_current_user)) -> UserOut:
    return serialize_user_out(user)


def require_platform_admin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

    if not is_platform_admin(get_platform_role_slug(user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a administradores")

    return user


def get_tenant_context(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantContext:
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Tenant-ID requerido",
        )

    tenant = db.query(Tenant).filter(
        (Tenant.id == x_tenant_id) | (Tenant.slug == x_tenant_id)
    ).first()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    if user.is_superadmin:
        return TenantContext(user=user, tenant=tenant, role="admin")

    membership = (
        db.query(TenantMembership)
        .filter(TenantMembership.tenant_id == tenant.id, TenantMembership.user_id == user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso al tenant")

    return TenantContext(user=user, tenant=tenant, role=membership.role)
