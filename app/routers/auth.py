from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, serialize_user_out
from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MessageResponse,
    RegisterRequest,
    SetupStoreRequest,
    SetupStoreResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(db: Session) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        return _service(db).login(payload)
    except AppError as exc:
        raise_http(exc)


@router.post("/register", response_model=LoginResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        return _service(db).register(payload)
    except AppError as exc:
        raise_http(exc)


@router.post("/google", response_model=LoginResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        return _service(db).google_login(payload)
    except AppError as exc:
        raise_http(exc)


@router.post("/setup-store", response_model=SetupStoreResponse)
def setup_store(
    payload: SetupStoreRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SetupStoreResponse:
    try:
        return _service(db).setup_store(user, payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/me", response_model=MeResponse)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    user = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).first()
    service = _service(db)
    tenants = service._tenants_for(user)
    return MeResponse(
        user=serialize_user_out(user),
        tenants=tenants,
        needs_store=not user.is_superadmin and len(tenants) == 0,
    )


@router.post("/logout", response_model=MessageResponse)
def logout() -> MessageResponse:
    return MessageResponse(message="Sesión cerrada")
