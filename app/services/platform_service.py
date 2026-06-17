from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.tenant_context import TenantContext
from app.models.license import TenantLicense
from app.models.platform_product import PlatformProduct
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import RoleOut
from app.schemas.license import LicenseCreate, LicenseOut, LicenseUpdate, PlatformProductOut
from app.schemas.platform_user import PlatformUserOut, PlatformUserRoleUpdate
from app.schemas.product import ProductOut
from app.services.base import BaseService
from app.utils.licenses import is_tenant_license_active


def _license_out(license_row: TenantLicense) -> LicenseOut:
    return LicenseOut(
        id=license_row.id,
        tenant_id=license_row.tenant_id,
        platform_product_id=license_row.platform_product_id,
        platform_product_name=license_row.platform_product.name,
        status=license_row.status,
        plan=license_row.plan,
        starts_at=license_row.starts_at,
        ends_at=license_row.ends_at,
        max_users=license_row.max_users,
        created_at=license_row.created_at,
    )


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


class LicenseService(BaseService):
    def __init__(self, db: Session, tenant_id: str | None = None):
        super().__init__(db)
        self.tenant_id = tenant_id

    def list_platform_products(self) -> list[PlatformProduct]:
        return (
            self.db.query(PlatformProduct)
            .filter(PlatformProduct.is_active.is_(True))
            .all()
        )

    def list_licenses(self) -> list[LicenseOut]:
        rows = (
            self.db.query(TenantLicense)
            .options(joinedload(TenantLicense.platform_product))
            .filter(TenantLicense.tenant_id == self.tenant_id)
            .order_by(TenantLicense.created_at.desc())
            .all()
        )
        return [_license_out(row) for row in rows]

    def create_license(self, ctx: TenantContext, payload: LicenseCreate) -> LicenseOut:
        if ctx.role != "admin" and not ctx.user.is_superadmin:
            raise ForbiddenError("Sin permisos")

        product = self.db.get(PlatformProduct, payload.platform_product_id)
        if product is None:
            raise NotFoundError("Producto Binfrix no encontrado")

        existing = (
            self.db.query(TenantLicense)
            .filter(
                TenantLicense.tenant_id == ctx.tenant.id,
                TenantLicense.platform_product_id == payload.platform_product_id,
            )
            .first()
        )
        if existing:
            raise AppError("Ya existe licencia para este producto")

        license_row = TenantLicense(
            tenant_id=ctx.tenant.id,
            platform_product_id=payload.platform_product_id,
            status=payload.status,
            plan=payload.plan,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            max_users=payload.max_users,
        )
        self.db.add(license_row)
        self.commit()
        self.db.refresh(license_row)
        return _license_out(license_row)

    def update_license(self, ctx: TenantContext, license_id: str, payload: LicenseUpdate) -> LicenseOut:
        if ctx.role != "admin" and not ctx.user.is_superadmin:
            raise ForbiddenError("Sin permisos")

        license_row = (
            self.db.query(TenantLicense)
            .filter(TenantLicense.id == license_id, TenantLicense.tenant_id == ctx.tenant.id)
            .first()
        )
        if license_row is None:
            raise NotFoundError("Licencia no encontrada")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(license_row, field, value)

        self.commit()
        self.db.refresh(license_row)
        return _license_out(license_row)


class ProductService(BaseService):
    def __init__(self, db: Session, tenant_id: str, user: User):
        super().__init__(db)
        self.tenant_id = tenant_id
        self.user = user

    def _license_map(self) -> dict[str, TenantLicense]:
        rows = (
            self.db.query(TenantLicense)
            .filter(TenantLicense.tenant_id == self.tenant_id)
            .all()
        )
        return {row.platform_product_id: row for row in rows}

    def _is_product_licensed(self, product_id: str, license_map: dict[str, TenantLicense]) -> bool:
        if self.user.is_superadmin:
            return True
        return is_tenant_license_active(license_map.get(product_id))

    def list_products(self) -> list[ProductOut]:
        products = (
            self.db.query(PlatformProduct)
            .filter(PlatformProduct.is_active.is_(True))
            .order_by(PlatformProduct.name)
            .all()
        )
        license_map = self._license_map()
        return [
            ProductOut(
                id=p.id,
                name=p.name,
                description=p.description,
                licensed=self._is_product_licensed(p.id, license_map),
                license_starts_at=license_map.get(p.id).starts_at if license_map.get(p.id) else None,
                license_ends_at=license_map.get(p.id).ends_at if license_map.get(p.id) else None,
            )
            for p in products
        ]

    def get_product(self, product_id: str) -> ProductOut:
        product = self.db.get(PlatformProduct, product_id)
        if product is None or not product.is_active:
            raise NotFoundError("Producto no encontrado")

        license_map = self._license_map()
        if not self._is_product_licensed(product_id, license_map):
            raise ForbiddenError("Sin licencia activa para este producto")

        return ProductOut(
            id=product.id,
            name=product.name,
            description=product.description,
            licensed=True,
        )


class RoleService(BaseService):
    def list_roles(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.name).all()

    def list_platform_users(self) -> list[PlatformUserOut]:
        users = (
            self.db.query(User)
            .options(joinedload(User.role))
            .order_by(User.name)
            .all()
        )
        return [_user_out(user) for user in users]

    def update_platform_user_role(self, user_id: str, payload: PlatformUserRoleUpdate) -> PlatformUserOut:
        role = self.db.query(Role).filter(Role.slug == payload.role).first()
        if role is None:
            raise AppError("Rol no válido")

        user = (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.id == user_id)
            .first()
        )
        if user is None:
            raise NotFoundError("Usuario no encontrado")

        user.role_id = role.id
        self.commit()
        self.db.refresh(user)
        return _user_out(user)
