from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.tenant_context import TenantContext
from app.models.catalog import CatalogProduct
from app.models.customer import Customer
from app.models.license import TenantLicense
from app.models.platform_product import PlatformProduct
from app.models.role import Role
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.core.security import get_password_hash
from app.core.roles import ROLE_CLIENT_1
from app.schemas.dashboard import ActivityOut, DashboardOut, StatOut
from app.schemas.platform_admin import (
    PlatformClientCreate,
    PlatformClientOut,
    PlatformLicenseCreate,
    PlatformLicenseOut,
    PlatformLicenseUpdate,
)
from app.utils.license_plans import (
    PRINCIPAL_MEMBERSHIP_ROLE,
    list_plan_definitions,
    resolve_plan_and_max_users,
)
from app.services.base import BaseService
from app.utils.catalog import get_display_price, get_total_stock, is_variable_product


class DashboardService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.tenant_id = tenant_id

    def _build_ecommerce_dashboard(self, ctx: TenantContext) -> DashboardOut:
        products = (
            self.db.query(CatalogProduct)
            .filter(CatalogProduct.tenant_id == self.tenant_id)
            .all()
        )
        customers = (
            self.db.query(Customer)
            .filter(Customer.tenant_id == self.tenant_id)
            .all()
        )

        active_products = sum(1 for p in products if p.status == "active")
        active_customers = sum(1 for c in customers if c.status == "active")
        without_stock = [p for p in products if get_total_stock(p.__dict__) == 0]
        units = sum(get_total_stock(p.__dict__) for p in products)
        stock_value = 0
        for product in products:
            pdata = product.__dict__
            if is_variable_product(product.product_type):
                for variant in product.variants or []:
                    stock_value += int(variant.get("price") or 0) * int(variant.get("stock") or 0)
            else:
                stock_value += int(product.price or 0) * int(product.stock or 0)

        stats = [
            StatOut(
                label="Productos en catálogo",
                value=str(len(products)),
                detail=f"{active_products} activos",
                tone="neutral",
                section="catalog",
            ),
            StatOut(
                label="Clientes registrados",
                value=str(len(customers)),
                detail=f"{active_customers} activos",
                tone="neutral",
                section="customers",
            ),
            StatOut(
                label="Unidades en stock",
                value=f"{units:,}".replace(",", "."),
                detail=f"{len(without_stock)} sin stock" if without_stock else "Inventario disponible",
                tone="warn" if without_stock else "good",
                section="catalog",
            ),
            StatOut(
                label="Valor del inventario",
                value=f"${stock_value:,}".replace(",", "."),
                detail="Valorización actual",
                tone="good",
                section="catalog",
            ),
        ]

        activity: list[ActivityOut] = []
        for customer in sorted(customers, key=lambda c: c.created_at, reverse=True)[:2]:
            activity.append(
                ActivityOut(
                    title="Cliente registrado",
                    subtitle=f"{customer.first_name} {customer.last_name}",
                    meta=customer.created_at.strftime("%d-%m-%Y"),
                )
            )
        for product in without_stock[:2]:
            activity.append(
                ActivityOut(
                    title="Producto sin stock",
                    subtitle=product.title,
                    meta=product.sku,
                )
            )

        highlights = [
            f"Catálogo con {len(products)} productos para tu ecommerce.",
            f"Precio desde ${get_display_price(products[0].__dict__):,}".replace(",", ".")
            if products
            else "Agrega productos al catálogo.",
        ]

        return DashboardOut(stats=stats, activity=activity[:5], highlights=highlights[:3])

    def get_summary(self, ctx: TenantContext, product_id: str) -> DashboardOut:
        product = self.db.get(PlatformProduct, product_id)
        if product is None:
            raise NotFoundError("Producto no encontrado")

        if not ctx.user.is_superadmin:
            license_row = (
                self.db.query(TenantLicense)
                .filter(
                    TenantLicense.tenant_id == self.tenant_id,
                    TenantLicense.platform_product_id == product_id,
                    TenantLicense.status == "active",
                )
                .first()
            )
            if license_row is None:
                raise ForbiddenError("Sin licencia activa para este módulo")

        if product_id in ("ecommerce-b2c", "ecommerce-b2b"):
            return self._build_ecommerce_dashboard(ctx)

        return DashboardOut(
            stats=[
                StatOut(label="Módulo activo", value=product.name, detail="Licencia vigente", tone="good"),
                StatOut(label="Tenant", value=ctx.tenant.name, detail=ctx.tenant.slug, tone="neutral"),
            ],
            activity=[
                ActivityOut(title="Panel listo", subtitle=product.description[:80], meta="Binfrix"),
            ],
            highlights=[f"Administrando {product.name} para {ctx.tenant.name}."],
        )


class PlatformAdminService(BaseService):
    def list_clients(self) -> list[PlatformClientOut]:
        tenants = self.db.query(Tenant).order_by(Tenant.name).all()
        results: list[PlatformClientOut] = []
        for tenant in tenants:
            licenses_count = (
                self.db.query(TenantLicense)
                .filter(TenantLicense.tenant_id == tenant.id)
                .count()
            )
            admin_membership = (
                self.db.query(TenantMembership)
                .options(joinedload(TenantMembership.user))
                .filter(
                    TenantMembership.tenant_id == tenant.id,
                    TenantMembership.role == "admin",
                )
                .first()
            )
            contact = admin_membership.user.email if admin_membership else ""
            created = tenant.created_at.date() if tenant.created_at else None
            results.append(
                PlatformClientOut(
                    id=tenant.id,
                    name=tenant.name,
                    slug=tenant.slug,
                    contact=contact,
                    status=tenant.status,
                    licenses_count=licenses_count,
                    created_at=created,
                )
            )
        return results

    def list_plans(self) -> list[dict[str, str | int]]:
        return list_plan_definitions()

    def create_client(self, payload: PlatformClientCreate) -> PlatformClientOut:
        if self.db.query(Tenant).filter(Tenant.slug == payload.slug).first():
            raise AppError("El slug ya está en uso")
        if self.db.query(User).filter(User.email == payload.principal_email.strip().lower()).first():
            raise AppError("El correo del usuario principal ya está registrado")

        client_role = self.db.query(Role).filter(Role.slug == ROLE_CLIENT_1).first()
        if client_role is None:
            raise AppError("Rol de cliente no configurado")

        tenant = Tenant(name=payload.name.strip(), slug=payload.slug.strip(), status="active")
        self.db.add(tenant)
        self.db.flush()

        principal = User(
            email=payload.principal_email.strip().lower(),
            name=payload.principal_name.strip(),
            password_hash=get_password_hash(payload.principal_password),
            role_id=client_role.id,
        )
        self.db.add(principal)
        self.db.flush()

        self.db.add(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=principal.id,
                role=PRINCIPAL_MEMBERSHIP_ROLE,
            )
        )
        self.commit()
        self.db.refresh(tenant)

        return PlatformClientOut(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            contact=principal.email,
            status=tenant.status,
            licenses_count=0,
            created_at=tenant.created_at.date() if tenant.created_at else None,
        )

    def list_all_licenses(self) -> list[PlatformLicenseOut]:
        rows = (
            self.db.query(TenantLicense)
            .options(
                joinedload(TenantLicense.tenant),
                joinedload(TenantLicense.platform_product),
            )
            .order_by(TenantLicense.created_at.desc())
            .all()
        )
        return [
            PlatformLicenseOut(
                id=row.id,
                tenant_id=row.tenant_id,
                client_name=row.tenant.name,
                product_name=row.platform_product.name,
                product_id=row.platform_product_id,
                plan=row.plan,
                status=row.status,
                starts_at=row.starts_at,
                ends_at=row.ends_at,
                max_users=row.max_users,
            )
            for row in rows
        ]

    def create_license(self, payload: PlatformLicenseCreate) -> PlatformLicenseOut:
        tenant = self.db.get(Tenant, payload.tenant_id)
        if tenant is None:
            raise NotFoundError("Cliente no encontrado")

        product = self.db.get(PlatformProduct, payload.platform_product_id)
        if product is None:
            raise NotFoundError("Producto Binfrix no encontrado")

        existing = (
            self.db.query(TenantLicense)
            .filter(
                TenantLicense.tenant_id == payload.tenant_id,
                TenantLicense.platform_product_id == payload.platform_product_id,
            )
            .first()
        )
        if existing:
            raise AppError("Ya existe licencia para este cliente y producto")

        plan, max_users = resolve_plan_and_max_users(payload.plan, payload.max_users)

        license_row = TenantLicense(
            tenant_id=payload.tenant_id,
            platform_product_id=payload.platform_product_id,
            status=payload.status,
            plan=plan,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            max_users=max_users,
        )
        self.db.add(license_row)
        self.commit()
        self.db.refresh(license_row)
        license_row = (
            self.db.query(TenantLicense)
            .options(
                joinedload(TenantLicense.tenant),
                joinedload(TenantLicense.platform_product),
            )
            .filter(TenantLicense.id == license_row.id)
            .first()
        )
        return PlatformLicenseOut(
            id=license_row.id,
            tenant_id=license_row.tenant_id,
            client_name=license_row.tenant.name,
            product_name=license_row.platform_product.name,
            product_id=license_row.platform_product_id,
            plan=license_row.plan,
            status=license_row.status,
            starts_at=license_row.starts_at,
            ends_at=license_row.ends_at,
            max_users=license_row.max_users,
        )

    def update_license(self, license_id: str, payload: PlatformLicenseUpdate) -> PlatformLicenseOut:
        license_row = (
            self.db.query(TenantLicense)
            .options(
                joinedload(TenantLicense.tenant),
                joinedload(TenantLicense.platform_product),
            )
            .filter(TenantLicense.id == license_id)
            .first()
        )
        if license_row is None:
            raise NotFoundError("Licencia no encontrada")

        data = payload.model_dump(exclude_unset=True)
        if "plan" in data or "max_users" in data:
            plan, max_users = resolve_plan_and_max_users(
                data.get("plan", license_row.plan),
                data.get("max_users", license_row.max_users),
            )
            data["plan"] = plan
            data["max_users"] = max_users

        for field, value in data.items():
            setattr(license_row, field, value)

        self.commit()
        self.db.refresh(license_row)
        return PlatformLicenseOut(
            id=license_row.id,
            tenant_id=license_row.tenant_id,
            client_name=license_row.tenant.name,
            product_name=license_row.platform_product.name,
            product_id=license_row.platform_product_id,
            plan=license_row.plan,
            status=license_row.status,
            starts_at=license_row.starts_at,
            ends_at=license_row.ends_at,
            max_users=license_row.max_users,
        )

    def delete_license(self, license_id: str) -> None:
        license_row = self.db.get(TenantLicense, license_id)
        if license_row is None:
            raise NotFoundError("Licencia no encontrada")
        self.db.delete(license_row)
        self.commit()

    def list_platform_products(self) -> list[PlatformProduct]:
        return (
            self.db.query(PlatformProduct)
            .filter(PlatformProduct.is_active.is_(True))
            .order_by(PlatformProduct.name)
            .all()
        )
