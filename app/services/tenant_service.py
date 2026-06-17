from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.security import get_password_hash
from app.core.tenant_context import TenantContext
from app.models.license import TenantLicense
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.auth import TenantSummary
from app.schemas.tenant import TenantCreate, TenantUserCreate, TenantUserOut, TenantUsersPageOut
from app.services.base import BaseService
from app.utils.license_plans import (
    PRINCIPAL_MEMBERSHIP_ROLE,
    STAFF_MEMBERSHIP_ROLE,
    max_users_for_plan,
)
from app.utils.licenses import is_tenant_license_active


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
        self.db.add(
            TenantMembership(tenant_id=tenant.id, user_id=user.id, role=PRINCIPAL_MEMBERSHIP_ROLE)
        )
        self.commit()
        return self.repo.refresh(tenant)

    def _tenant_user_limit(self, tenant_id: str) -> int:
        licenses = (
            self.db.query(TenantLicense)
            .filter(TenantLicense.tenant_id == tenant_id)
            .all()
        )
        active_limits = [
            row.max_users or max_users_for_plan(row.plan)
            for row in licenses
            if is_tenant_license_active(row)
        ]
        if not active_limits:
            return 1
        return max(active_limits)

    def _membership_out(self, membership: TenantMembership) -> TenantUserOut:
        return TenantUserOut(
            id=membership.id,
            user_id=membership.user.id,
            email=membership.user.email,
            name=membership.user.name,
            role=membership.role,
            is_principal=membership.role == PRINCIPAL_MEMBERSHIP_ROLE,
        )

    def list_tenant_users_page(self, ctx: TenantContext) -> TenantUsersPageOut:
        memberships = (
            self.db.query(TenantMembership)
            .options(joinedload(TenantMembership.user), joinedload(TenantMembership.tenant))
            .filter(TenantMembership.tenant_id == ctx.tenant.id)
            .all()
        )
        max_users = self._tenant_user_limit(ctx.tenant.id)
        current_users = len(memberships)
        can_invite = (
            ctx.role == PRINCIPAL_MEMBERSHIP_ROLE or ctx.user.is_superadmin
        ) and current_users < max_users

        return TenantUsersPageOut(
            max_users=max_users,
            current_users=current_users,
            can_invite=can_invite,
            users=[self._membership_out(m) for m in memberships],
        )

    def add_tenant_user(self, ctx: TenantContext, payload: TenantUserCreate) -> TenantUserOut:
        if ctx.role != PRINCIPAL_MEMBERSHIP_ROLE and not ctx.user.is_superadmin:
            raise ForbiddenError("Solo el usuario principal puede crear otros usuarios")

        max_users = self._tenant_user_limit(ctx.tenant.id)
        current_users = (
            self.db.query(TenantMembership)
            .filter(TenantMembership.tenant_id == ctx.tenant.id)
            .count()
        )
        if current_users >= max_users:
            raise AppError(f"Límite de usuarios alcanzado ({max_users})")

        if payload.role == PRINCIPAL_MEMBERSHIP_ROLE:
            raise AppError("No se puede crear otro usuario principal")

        email = payload.email.strip().lower()
        user = self.db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                name=payload.name.strip(),
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
            raise AppError("El usuario ya pertenece al cliente")

        membership = TenantMembership(
            tenant_id=ctx.tenant.id,
            user_id=user.id,
            role=STAFF_MEMBERSHIP_ROLE,
        )
        self.db.add(membership)
        self.commit()
        self.db.refresh(membership)
        membership.user = user

        return self._membership_out(membership)

    def get_tenant_by_id_or_slug(self, tenant_key: str) -> Tenant:
        tenant = (
            self.db.query(Tenant)
            .filter((Tenant.id == tenant_key) | (Tenant.slug == tenant_key))
            .first()
        )
        if tenant is None:
            raise NotFoundError("Tenant no encontrado")
        return tenant
