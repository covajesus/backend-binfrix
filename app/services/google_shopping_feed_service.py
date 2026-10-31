"""Build Google Merchant Center product feeds from the store catalog.

Merchant Center schedules a fetch of the public XML URL; each active catalog
product is included automatically (no per-product push required for the feed).
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import AppError, NotFoundError
from app.models.catalog import CatalogProduct
from app.models.store_settings import StoreSettings
from app.models.tenant import Tenant
from app.services.base import BaseService


def _xml_text(value: str) -> str:
    return escape((value or "").strip())


def _first_image(images) -> str:
    if not isinstance(images, list) or not images:
        return ""
    first = images[0]
    if isinstance(first, str):
        return first.strip()
    if isinstance(first, dict):
        return str(first.get("url") or first.get("src") or "").strip()
    return ""


def _money(amount: int, currency: str) -> str:
    currency = (currency or "CLP").upper()
    # Catalog prices are stored as whole major units (e.g. CLP pesos).
    return f"{int(amount or 0)} {currency}"


class GoogleShoppingFeedService(BaseService):
    """Generate Google Shopping RSS XML for a tenant storefront."""

    def __init__(self, db: Session):
        super().__init__(db)

    def _tenant(self, slug: str) -> Tenant:
        tenant = (
            self.db.query(Tenant)
            .filter(Tenant.slug == slug, Tenant.status == "active")
            .first()
        )
        if tenant is None:
            raise NotFoundError("Tienda no encontrada")
        return tenant

    def _settings_row(self, tenant_id: str) -> StoreSettings | None:
        return (
            self.db.query(StoreSettings)
            .filter(StoreSettings.tenant_id == tenant_id)
            .first()
        )

    def feed_url_for_slug(self, slug: str) -> str:
        base = get_settings().api_public_url.rstrip("/")
        return f"{base}/api/v1/store/{slug}/feeds/google-shopping.xml"

    def build_xml(self, tenant_slug: str) -> str:
        tenant = self._tenant(tenant_slug)
        row = self._settings_row(tenant.id)
        if row is None or not bool(getattr(row, "google_shopping_enabled", False)):
            raise AppError("Google Shopping feed is not enabled for this store", 404)

        store_url = (row.store_url or "").strip().rstrip("/")
        if not store_url:
            store_url = f"https://{tenant.slug}.binfrix.io"

        language = (getattr(row, "google_shopping_language", None) or "es").strip().lower()
        country = (getattr(row, "google_shopping_country", None) or "CL").strip().upper()
        currency = (getattr(row, "google_shopping_currency", None) or "CLP").strip().upper()
        brand = (
            (getattr(row, "google_shopping_brand", None) or "").strip()
            or tenant.name
            or tenant.slug
        )

        products = (
            self.db.query(CatalogProduct)
            .filter(
                CatalogProduct.tenant_id == tenant.id,
                CatalogProduct.status == "active",
            )
            .order_by(CatalogProduct.title)
            .all()
        )

        title = _xml_text(f"{tenant.name or tenant.slug} products")
        link = _xml_text(store_url)
        description = _xml_text(f"Google Shopping feed for {tenant.name or tenant.slug}")

        items: list[str] = []
        for product in products:
            image = _first_image(product.images)
            if not image:
                continue
            offer_id = (product.sku or product.id or "").strip()
            if not offer_id:
                continue
            product_link = f"{store_url}/product/{product.id}"
            availability = "in_stock" if int(product.stock or 0) > 0 else "out_of_stock"
            desc = (product.description or product.title or "").strip()
            # Google requires non-empty description.
            if not desc:
                desc = product.title
            product_type = (product.category or "").strip()

            items.append(
                "\n".join(
                    [
                        "    <item>",
                        f"      <g:id>{_xml_text(offer_id)}</g:id>",
                        f"      <g:title>{_xml_text(product.title)}</g:title>",
                        f"      <g:description>{_xml_text(desc)}</g:description>",
                        f"      <g:link>{_xml_text(product_link)}</g:link>",
                        f"      <g:image_link>{_xml_text(image)}</g:image_link>",
                        f"      <g:availability>{availability}</g:availability>",
                        f"      <g:price>{_money(product.price, currency)}</g:price>",
                        f"      <g:condition>new</g:condition>",
                        f"      <g:brand>{_xml_text(brand)}</g:brand>",
                        f"      <g:identifier_exists>false</g:identifier_exists>",
                        f"      <g:adult>no</g:adult>",
                        (
                            f"      <g:product_type>{_xml_text(product_type)}</g:product_type>"
                            if product_type
                            else ""
                        ),
                        f"      <!-- target {country}/{language} -->",
                        "    </item>",
                    ]
                )
            )

        body = "\n".join(line for line in items if line.strip())
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
            "  <channel>\n"
            f"    <title>{title}</title>\n"
            f"    <link>{link}</link>\n"
            f"    <description>{description}</description>\n"
            f"{body}\n"
            "  </channel>\n"
            "</rss>\n"
        )
