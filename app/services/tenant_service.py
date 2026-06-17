from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.security import get_password_hash
from app.core.tenant_context import TenantContext
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.auth import TenantSummary
from app.schemas.tenant import TenantCreate, TenantUserCreate, TenantUserOut
from app.services.base import BaseService


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    def __init__(self, db: Session):
        super().__init__(db, tenant_id=None)


class TenantService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = TenantRepository(db)

    def list_for_user(self, user: User) -> list[TenantSummary]:
        if user.is_superadmin:
            tenants = self.db.query(Tenant).order_by(Tenant.name).all()
            return [
                TenantSummary(id=t.id, name=t.name, slug=t.slug, role="admin")
                for t in tenants
            ]

        memberships = (
            self.db.query(TenantMembership)
            .filter(TenantMembership.user_id == user.id)
            .all()
        )
        return [
            TenantSummary(
                id=m.tenant.id,
                name=m.tenant.name,
                slug=m.tenant.slug,
                role=m.role,
            )
            for m in memberships
        ]

    def create_tenant(self, payload: TenantCreate, user: User) -> Tenant:
        if self.db.query(Tenant).filter(Tenant.slug == payload.slug).first():
            raise AppError("El slug ya está en uso")

        tenant = Tenant(name=payload.name, slug=payload.slug, status="active")
        self.repo.add(tenant)
        self.db.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role="admin"))
        self.commit()
        return self.repo.refresh(tenant)

    def list_tenant_users(self, tenant_id: str) -> list[TenantUserOut]:
        memberships = (
            self.db.query(TenantMembership)
            .filter(TenantMembership.tenant_id == tenant_id)
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

    def add_tenant_user(self, ctx: TenantContext, payload: TenantUserCreate) -> TenantUserOut:
        if ctx.role not in ("admin",) and not ctx.user.is_superadmin:
            raise ForbiddenError("Solo administradores pueden invitar usuarios")

        user = self.db.query(User).filter(User.email == payload.email).first()
        if user is None:
            user = User(
                email=payload.email,
                name=payload.name,
                password_hash=get_password_hash(payload.password),
            )
            self.db.add(user)
            self.db.flush()

        existing = (
            self.db.query(TenantMembership)
            .filter(
                TenantMembership.tenant_id == ctx.tenant.id,
                TenantMembership.user_id == user.id,
            )
            .first()
        )
        if existing:
            raise AppError("El usuario ya pertenece al tenant")

        membership = TenantMembership(
            tenant_id=ctx.tenant.id,
            user_id=user.id,
            role=payload.role,
        )
        self.db.add(membership)
        self.commit()
        self.db.refresh(membership)

        return TenantUserOut(
            id=membership.id,
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=membership.role,
        )

    def get_tenant_by_id_or_slug(self, tenant_key: str) -> Tenant:
        tenant = (
            self.db.query(Tenant)
            .filter((Tenant.id == tenant_key) | (Tenant.slug == tenant_key))
            .first()
        )
        if tenant is None:
            raise NotFoundError("Tenant no encontrado")
        return tenant
