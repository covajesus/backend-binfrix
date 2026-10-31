"""Seed sample storefront content for newly provisioned tenants."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.demo_assets import STORE_LOGO_URL
from app.db.help_seed_data import DEMO_HELP_PAGES
from app.db.sports_seed_content import (
    DEMO_PRODUCT_SPECS,
    build_catalog_product,
    build_demo_categories,
    build_demo_sliders,
)
from app.db.store_settings_seed_data import DEMO_STORE_SETTINGS
from app.models.catalog import CatalogProduct
from app.models.help_page import HelpPage
from app.models.slider import Slider
from app.models.store_settings import StoreSettings
from app.services.base import BaseService


class StoreSampleService(BaseService):
    """Populate categories, products, sliders, help, and a sample logo."""

    def __init__(self, db: Session):
        super().__init__(db)

    def seed_new_store(
        self,
        tenant_id: str,
        *,
        store_name: str,
        store_url: str,
    ) -> None:
        """Idempotent sample catalog for a brand-new tenant store."""
        if (
            self.db.query(CatalogProduct)
            .filter(CatalogProduct.tenant_id == tenant_id)
            .first()
        ):
            return

        self.db.add_all(build_demo_categories(tenant_id))

        if not self.db.query(Slider).filter(Slider.tenant_id == tenant_id).first():
            self.db.add_all(build_demo_sliders(tenant_id))

        for spec in DEMO_PRODUCT_SPECS:
            self.db.add(build_catalog_product(tenant_id, spec))

        if not self.db.query(HelpPage).filter(HelpPage.tenant_id == tenant_id).first():
            for page_data in DEMO_HELP_PAGES:
                self.db.add(
                    HelpPage(
                        tenant_id=tenant_id,
                        slug=page_data["slug"],
                        nav_label=page_data["nav_label"],
                        title=page_data["title"],
                        subtitle=page_data["subtitle"],
                        intro=page_data["intro"],
                        sections=page_data["sections"],
                        sort_order=page_data["sort_order"],
                        status="active",
                    )
                )

        settings = (
            self.db.query(StoreSettings)
            .filter(StoreSettings.tenant_id == tenant_id)
            .first()
        )
        if settings is None:
            settings = StoreSettings(tenant_id=tenant_id)
            self.db.add(settings)
            self.db.flush()

        settings.phone = DEMO_STORE_SETTINGS["phone"]
        settings.schedule = DEMO_STORE_SETTINGS["schedule"]
        settings.support_label = DEMO_STORE_SETTINGS["support_label"]
        settings.support_href = DEMO_STORE_SETTINGS["support_href"]
        settings.contact_email = DEMO_STORE_SETTINGS["contact_email"]
        settings.store_url = store_url
        settings.store_logo_url = STORE_LOGO_URL
        settings.storefront_template = DEMO_STORE_SETTINGS.get(
            "storefront_template", "lamora"
        )
        settings.multilingual_enabled = DEMO_STORE_SETTINGS.get(
            "multilingual_enabled", False
        )
        settings.default_locale = DEMO_STORE_SETTINGS.get("default_locale", "es")
        settings.account_label = DEMO_STORE_SETTINGS.get("account_label", "Cuenta")
        settings.account_href = DEMO_STORE_SETTINGS.get("account_href", "/account")
        settings.promo_messages = list(DEMO_STORE_SETTINGS.get("promo_messages", []))
        settings.header_links = list(DEMO_STORE_SETTINGS.get("header_links", []))
        settings.social_links = list(DEMO_STORE_SETTINGS.get("social_links", []))
        # Soft branding hint in promo strip
        if store_name:
            settings.promo_messages = [
                f"Bienvenido a {store_name}",
                *list(settings.promo_messages or [])[:2],
            ]

        self.db.flush()
