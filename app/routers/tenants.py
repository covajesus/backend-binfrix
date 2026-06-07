from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_context
from app.core.security import get_password_hash
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.schemas.auth import TenantSummary
from app.schemas.tenant import TenantCreate, TenantOut, TenantUserCreate, TenantUserOut

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantSummary])
def list_tenants(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TenantSummary]:
    if user.is_superadmin:
        return [
            TenantSummary(id=t.id, name=t.name, slug=t.slug, role="admin")
            for t in db.query(Tenant).order_by(Tenant.name).all()
        ]

    memberships = db.query(TenantMembership).filter(TenantMembership.user_id == user.id).all()
    return [
        TenantSummary(
            id=m.tenant.id,
            name=m.tenant.name,
            slug=m.tenant.slug,
            role=m.role,
        )
        for m in memberships
    ]


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tenant:
    if db.query(Tenant).filter(Tenant.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="El slug ya está en uso")

    tenant = Tenant(name=payload.name, slug=payload.slug, status="active")
    db.add(tenant)
    db.flush()
    db.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role="admin"))
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/current", response_model=TenantOut)
def current_tenant(ctx: TenantContext = Depends(get_tenant_context)) -> Tenant:
    return ctx.tenant


@router.post("/users", response_model=TenantUserOut, status_code=status.HTTP_201_CREATED)
def add_tenant_user(
    payload: TenantUserCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> TenantUserOut:
    if ctx.role not in ("admin",) and not ctx.user.is_superadmin:
        raise HTTPException(status_code=403, detail="Solo administradores pueden invitar usuarios")

    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        user = User(
            email=payload.email,
            name=payload.name,
            password_hash=get_password_hash(payload.password),
        )
        db.add(user)
        db.flush()

    existing = (
        db.query(TenantMembership)
        .filter(
            TenantMembership.tenant_id == ctx.tenant.id,
            TenantMembership.user_id == user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya pertenece al tenant")

    membership = TenantMembership(
        tenant_id=ctx.tenant.id,
        user_id=user.id,
        role=payload.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return TenantUserOut(
        id=membership.id,
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=membership.role,
    )


@router.get("/users", response_model=list[TenantUserOut])
def list_tenant_users(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[TenantUserOut]:
    memberships = (
        db.query(TenantMembership)
        .filter(TenantMembership.tenant_id == ctx.tenant.id)
        .all()
    )
    return [
        TenantUserOut(
            id=m.id,
            user_id=m.user.id,
            email=m.user.email,
            name=m.user.name,
            role=m.role,
        )
        for m in memberships
    ]
