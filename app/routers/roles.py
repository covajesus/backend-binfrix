from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_platform_admin
from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RoleOut
from app.schemas.platform_user import PlatformUserOut, PlatformUserRoleUpdate
from app.services.platform_service import RoleService

router = APIRouter(tags=["roles"])


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[RoleOut]:
    return RoleService(db).list_roles()


@router.get("/platform-users", response_model=list[PlatformUserOut])
def list_platform_users(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformUserOut]:
    return RoleService(db).list_platform_users()


@router.patch("/platform-users/{user_id}/role", response_model=PlatformUserOut)
def update_platform_user_role(
    user_id: str,
    payload: PlatformUserRoleUpdate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> PlatformUserOut:
    try:
        return RoleService(db).update_platform_user_role(user_id, payload)
    except AppError as exc:
        raise_http(exc)
