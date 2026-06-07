from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, require_platform_admin
from app.core.roles import PLATFORM_ROLES
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import RoleOut
from app.schemas.platform_user import PlatformUserOut, PlatformUserRoleUpdate

router = APIRouter(tags=["roles"])


def _user_out(user: User) -> PlatformUserOut:
    role_slug = user.role.slug if user.role else ""
    return PlatformUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=role_slug,
        role_name=user.role.name if user.role else "",
        status="active",
        created_at=user.created_at.date() if user.created_at else None,
    )


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[Role]:
    return db.query(Role).order_by(Role.name).all()


@router.get("/platform-users", response_model=list[PlatformUserOut])
def list_platform_users(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformUserOut]:
    users = (
        db.query(User)
        .options(joinedload(User.role))
        .order_by(User.name)
        .all()
    )
    return [_user_out(user) for user in users]


@router.patch("/platform-users/{user_id}/role", response_model=PlatformUserOut)
def update_platform_user_role(
    user_id: str,
    payload: PlatformUserRoleUpdate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> PlatformUserOut:
    role = db.query(Role).filter(Role.slug == payload.role).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol no válido")

    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.id == user_id)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return _user_out(user)
