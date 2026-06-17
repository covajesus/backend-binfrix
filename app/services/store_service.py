"""API pública storefront — sin auth, scoped por slug de tenant."""

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.catalog import CatalogProduct
from app.models.category import Category
from app.models.customer import Customer
from app.models.license import TenantLicense
from app.models.order import Order
from app.models.slider import Slider
from app.models.help_page import HelpPage
from app.models.store_settings import StoreSettings
from app.models.tenant import Tenant
from app.schemas.order import OrderCreate
from app.schemas.store_settings import StoreSettingsPublicOut
from app.services.base import BaseService
from app.services.store_settings_service import StoreSettingsService
from app.utils.orders import calc_order_total, generate_order_number, normalize_line_items, today


class StoreService(BaseService):
    ECOMMERCE_PRODUCTS = ("ecommerce-b2c", "ecommerce-b2b")

    def _get_public_tenant(self, slug: str) -> Tenant:
        tenant = (
            self.db.query(Tenant)
            .filter(Tenant.slug == slug, Tenant.status == "active")
            .first()
        )
        if tenant is None:
            raise NotFoundError("Tienda no encontrada")

        license_row = (
            self.db.query(TenantLicense)
            .filter(
                TenantLicense.tenant_id == tenant.id,
                TenantLicense.platform_product_id.in_(self.ECOMMERCE_PRODUCTS),
                TenantLicense.status == "active",
            )
            .first()
        )
        if license_row is None:
            raise ForbiddenError("Tienda sin licencia ecommerce activa")

        return tenant

    def get_store_info(self, tenant_slug: str) -> dict:
        tenant = self._get_public_tenant(tenant_slug)
        return {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
        }

    def get_store_info_by_id(self, tenant_id: str) -> dict:
        row = (
            self.db.query(Tenant)
            .filter(Tenant.id == tenant_id, Tenant.status == "active")
            .first()
        )
        if row is None:
            raise NotFoundError("Tienda no encontrada")
        tenant = self._get_public_tenant(row.slug)
        return {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
        }

    def get_store_settings(self, tenant_slug: str) -> StoreSettingsPublicOut:
        tenant = self._get_public_tenant(tenant_slug)
        return StoreSettingsService(self.db).get_or_create_public(tenant.id)

    def list_categories(self, tenant_slug: str) -> list[Category]:
        tenant = self._get_public_tenant(tenant_slug)
        return (
            self.db.query(Category)
            .filter(Category.tenant_id == tenant.id, Category.status == "active")
            .order_by(Category.name)
            .all()
        )

    def list_sliders(self, tenant_slug: str) -> list[Slider]:
        tenant = self._get_public_tenant(tenant_slug)
        return (
            self.db.query(Slider)
            .filter(Slider.tenant_id == tenant.id, Slider.status == "active")
            .order_by(Slider.sort_order, Slider.created_at)
            .all()
        )

    def list_help_pages(self, tenant_slug: str) -> list[HelpPage]:
        tenant = self._get_public_tenant(tenant_slug)
        return (
            self.db.query(HelpPage)
            .filter(HelpPage.tenant_id == tenant.id, HelpPage.status == "active")
            .order_by(HelpPage.sort_order, HelpPage.title)
            .all()
        )

    def get_help_page(self, tenant_slug: str, page_slug: str) -> HelpPage:
        tenant = self._get_public_tenant(tenant_slug)
        page = (
            self.db.query(HelpPage)
            .filter(
                HelpPage.tenant_id == tenant.id,
                HelpPage.slug == page_slug.strip().lower(),
                HelpPage.status == "active",
            )
            .first()
        )
        if page is None:
            raise NotFoundError("Página de ayuda no encontrada")
        return page

    def list_catalog(self, tenant_slug: str) -> list[CatalogProduct]:
        tenant = self._get_public_tenant(tenant_slug)
        return (
            self.db.query(CatalogProduct)
            .filter(CatalogProduct.tenant_id == tenant.id, CatalogProduct.status == "active")
            .order_by(CatalogProduct.title)
            .all()
        )

    def get_catalog_item(self, tenant_slug: str, item_id: str) -> CatalogProduct:
        tenant = self._get_public_tenant(tenant_slug)
        item = (
            self.db.query(CatalogProduct)
            .filter(
                CatalogProduct.id == item_id,
                CatalogProduct.tenant_id == tenant.id,
                CatalogProduct.status == "active",
            )
            .first()
        )
        if item is None:
            raise NotFoundError("Producto no encontrado")
        return item

    def create_order(
        self,
        tenant_slug: str,
        payload: OrderCreate,
        customer: Customer | None = None,
    ) -> Order:
        tenant = self._get_public_tenant(tenant_slug)
        count = self.db.query(Order).filter(Order.tenant_id == tenant.id).count()
        items = normalize_line_items([item.model_dump() for item in payload.items])

        customer_id = payload.customer_id
        customer_name = payload.customer_name.strip()
        customer_email = payload.customer_email
        customer_phone = payload.customer_phone
        city = payload.city

        if customer is not None:
            customer_id = customer.id
            if not customer_name:
                customer_name = f"{customer.first_name} {customer.last_name}".strip()
            if not customer_email:
                customer_email = customer.email
            if not customer_phone:
                customer_phone = customer.phone
            if not city:
                city = customer.city

        order = Order(
            tenant_id=tenant.id,
            order_number=generate_order_number(count),
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=payload.shipping_address,
            city=city,
            status="pending",
            payment_status="pending",
            items=items,
            total=calc_order_total(items) + int(payload.shipping_amount or 0),
            notes=payload.notes,
            created_at=today(),
        )
        self.db.add(order)
        self.commit()
        self.db.refresh(order)
        return order
