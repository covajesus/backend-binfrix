import re

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError
from app.db.store_settings_seed_data import DEMO_STORE_SETTINGS
from app.models.store_settings import StoreSettings
from app.repositories.base import BaseRepository
from app.schemas.store_settings import (
    ALLOWED_BILLING_COUNTRIES,
    ALLOWED_LOCALES,
    ALLOWED_PAYMENT_GATEWAY_ENVIRONMENTS,
    ALLOWED_SOCIAL_IDS,
    ALLOWED_STOREFRONT_TEMPLATES,
    StoreSettingsOut,
    StoreSettingsPublicOut,
    StoreSettingsUpdate,
)
from app.services.base import BaseService
from app.services.custom_storefront_template_service import CustomStorefrontTemplateService
from app.utils.store_theme import merge_theme_colors, serialize_theme_colors_update


class StoreSettingsRepository(BaseRepository[StoreSettings]):
    model = StoreSettings

    def get_row(self) -> StoreSettings | None:
        if not self.tenant_id:
            return None
        return self._base_query().first()

    def require_row(self, message: str = "Configuración de tienda no encontrada") -> StoreSettings:
        row = self.get_row()
        if row is None:
            raise AppError(message, 400)
        return row


def _phone_href(phone: str) -> str:
    digits = re.sub(r"[^\d+]", "", phone or "")
    return f"tel:{digits}" if digits else ""


def _link_value(link, key: str, default: str | bool = "") -> str | bool:
    if isinstance(link, dict):
        return link.get(key, default)
    return getattr(link, key, default)


def _serialize_social_links(links: list) -> list[dict]:
    result: list[dict] = []
    for link in links:
        network_id = str(_link_value(link, "id")).strip().lower()
        if network_id not in ALLOWED_SOCIAL_IDS:
            raise ConflictError(f"Red social no válida: {network_id}")
        href = str(_link_value(link, "href")).strip()
        if not href:
            continue
        result.append(
            {
                "id": network_id,
                "label": str(_link_value(link, "label")).strip(),
                "href": href,
                "show_in_header": bool(_link_value(link, "show_in_header", False)),
                "show_in_footer": bool(_link_value(link, "show_in_footer", False)),
            }
        )
    return result


def _serialize_header_links(links: list) -> list[dict]:
    result: list[dict] = []
    for link in links:
        label = str(_link_value(link, "label")).strip()
        href = str(_link_value(link, "href")).strip()
        if not label or not href:
            continue
        group = str(_link_value(link, "group", "left")).strip().lower()
        if group not in {"left", "right"}:
            group = "left"
        result.append({"label": label, "href": href, "group": group})
    return result


def _serialize_promo_messages(messages: list) -> list[str]:
    result: list[str] = []
    for message in messages:
        text = str(message).strip()
        if text:
            result.append(text)
    return result


def _to_out(row: StoreSettings) -> StoreSettingsOut:
    defaults = DEMO_STORE_SETTINGS
    template_id = row.storefront_template or "sports"
    return StoreSettingsOut(
        phone=row.phone or "",
        phone_href=_phone_href(row.phone),
        schedule=row.schedule or "",
        support_label=row.support_label or "",
        support_href=row.support_href or "/help",
        contact_email=row.contact_email or "",
        store_url=row.store_url or "",
        store_logo_url=row.store_logo_url or "",
        storefront_template=template_id,
        multilingual_enabled=bool(row.multilingual_enabled),
        default_locale=row.default_locale or "es",
        account_label=row.account_label or defaults.get("account_label", ""),
        account_href=row.account_href or defaults.get("account_href", "/help"),
        promo_messages=row.promo_messages or list(defaults.get("promo_messages", [])),
        header_links=row.header_links or list(defaults.get("header_links", [])),
        social_links=row.social_links or [],
        theme_colors=merge_theme_colors(template_id, row.theme_colors or {}),
        payment_gateway_enabled=bool(row.payment_gateway_enabled),
        payment_gateway_provider=row.payment_gateway_provider or "",
        payment_gateway_merchant_id=row.payment_gateway_merchant_id or "",
        payment_gateway_environment=row.payment_gateway_environment or "sandbox",
        payment_gateway_api_key_configured=bool((row.payment_gateway_api_key or "").strip()),
        billing_enabled=bool(row.billing_enabled),
        billing_country=row.billing_country or "CL",
        billing_provider=row.billing_provider or "",
        billing_api_key_configured=bool((row.billing_api_key or "").strip()),
        billing_username=row.billing_username or "",
        billing_branch=row.billing_branch or "Casa Matriz",
        billing_emitter_rut=row.billing_emitter_rut or "",
        billing_emitter_name=row.billing_emitter_name or "",
        billing_emitter_activity=row.billing_emitter_activity or "",
        billing_emitter_address=row.billing_emitter_address or "",
        billing_emitter_commune=row.billing_emitter_commune or "",
        billing_emitter_city=row.billing_emitter_city or "",
        updated_at=row.updated_at,
    )


def _to_public_out(row: StoreSettings) -> StoreSettingsPublicOut:
    admin = _to_out(row)
    return StoreSettingsPublicOut(
        phone=admin.phone,
        phone_href=admin.phone_href,
        schedule=admin.schedule,
        support_label=admin.support_label,
        support_href=admin.support_href,
        contact_email=admin.contact_email,
        store_url=admin.store_url,
        store_logo_url=admin.store_logo_url,
        storefront_template=admin.storefront_template,
        multilingual_enabled=admin.multilingual_enabled,
        default_locale=admin.default_locale,
        account_label=admin.account_label,
        account_href=admin.account_href,
        promo_messages=admin.promo_messages,
        header_links=admin.header_links,
        social_links=admin.social_links,
        theme_colors=admin.theme_colors,
        payment_gateway_enabled=admin.payment_gateway_enabled,
        payment_gateway_provider=admin.payment_gateway_provider,
    )


class StoreSettingsService(BaseService):
    def __init__(self, db: Session, tenant_id: str | None = None):
        super().__init__(db)
        self.tenant_id = tenant_id

    def _defaults(self) -> dict:
        return {
            "phone": DEMO_STORE_SETTINGS["phone"],
            "schedule": DEMO_STORE_SETTINGS["schedule"],
            "support_label": DEMO_STORE_SETTINGS["support_label"],
            "support_href": DEMO_STORE_SETTINGS["support_href"],
            "contact_email": DEMO_STORE_SETTINGS["contact_email"],
            "store_url": DEMO_STORE_SETTINGS["store_url"],
            "store_logo_url": DEMO_STORE_SETTINGS.get("store_logo_url", ""),
            "storefront_template": DEMO_STORE_SETTINGS.get("storefront_template", "sports"),
            "multilingual_enabled": DEMO_STORE_SETTINGS.get("multilingual_enabled", False),
            "default_locale": DEMO_STORE_SETTINGS.get("default_locale", "es"),
            "account_label": DEMO_STORE_SETTINGS.get("account_label", ""),
            "account_href": DEMO_STORE_SETTINGS.get("account_href", "/help"),
            "promo_messages": list(DEMO_STORE_SETTINGS.get("promo_messages", [])),
            "header_links": list(DEMO_STORE_SETTINGS.get("header_links", [])),
            "social_links": list(DEMO_STORE_SETTINGS["social_links"]),
            "theme_colors": {},
        }

    def _get_row(self, tenant_id: str) -> StoreSettings | None:
        return StoreSettingsRepository(self.db, tenant_id=tenant_id).get_row()

    def get_or_create(self, tenant_id: str) -> StoreSettingsOut:
        row = self._get_row(tenant_id)
        if row is None:
            defaults = self._defaults()
            row = StoreSettings(tenant_id=tenant_id, **defaults)
            self.db.add(row)
            self.commit()
            row = self._get_row(tenant_id)
        return _to_out(row)

    def get_or_create_public(self, tenant_id: str) -> StoreSettingsPublicOut:
        row = self._get_row(tenant_id)
        if row is None:
            defaults = self._defaults()
            row = StoreSettings(tenant_id=tenant_id, **defaults)
            self.db.add(row)
            self.commit()
            row = self._get_row(tenant_id)
        return _to_public_out(row)

    def get_settings(self) -> StoreSettingsOut:
        if not self.tenant_id:
            raise ConflictError("Tenant no definido")
        return self.get_or_create(self.tenant_id)

    def update_settings(self, payload: StoreSettingsUpdate) -> StoreSettingsOut:
        if not self.tenant_id:
            raise ConflictError("Tenant no definido")

        row = self._get_row(self.tenant_id)
        if row is None:
            defaults = self._defaults()
            row = StoreSettings(tenant_id=self.tenant_id, **defaults)
            self.db.add(row)

        data = payload.model_dump(exclude_unset=True)
        if "phone" in data and data["phone"] is not None:
            data["phone"] = data["phone"].strip()
        if "schedule" in data and data["schedule"] is not None:
            data["schedule"] = data["schedule"].strip()
        if "support_label" in data and data["support_label"] is not None:
            data["support_label"] = data["support_label"].strip()
        if "support_href" in data and data["support_href"] is not None:
            data["support_href"] = data["support_href"].strip() or "/help"
        if "contact_email" in data and data["contact_email"] is not None:
            data["contact_email"] = data["contact_email"].strip()
        if "store_url" in data and data["store_url"] is not None:
            data["store_url"] = data["store_url"].strip()
        if "store_logo_url" in data and data["store_logo_url"] is not None:
            data["store_logo_url"] = data["store_logo_url"].strip()
        if "storefront_template" in data and data["storefront_template"] is not None:
            template_id = data["storefront_template"].strip().lower()
            if not CustomStorefrontTemplateService.is_allowed_template_id(
                self.db,
                self.tenant_id,
                template_id,
            ):
                raise ConflictError(f"Plantilla no válida: {template_id}")
            data["storefront_template"] = template_id
        if "default_locale" in data and data["default_locale"] is not None:
            locale = data["default_locale"].strip().lower()
            if locale not in ALLOWED_LOCALES:
                raise ConflictError(f"Idioma no válido: {locale}")
            data["default_locale"] = locale
        if "multilingual_enabled" in data and data["multilingual_enabled"] is not None:
            data["multilingual_enabled"] = bool(data["multilingual_enabled"])
        if "account_label" in data and data["account_label"] is not None:
            data["account_label"] = data["account_label"].strip()
        if "account_href" in data and data["account_href"] is not None:
            data["account_href"] = data["account_href"].strip() or "/help"
        if "promo_messages" in data and data["promo_messages"] is not None:
            data["promo_messages"] = _serialize_promo_messages(data["promo_messages"])
        if "header_links" in data and data["header_links"] is not None:
            data["header_links"] = _serialize_header_links(data["header_links"])
        if "social_links" in data and data["social_links"] is not None:
            data["social_links"] = _serialize_social_links(data["social_links"])
        if "theme_colors" in data and data["theme_colors"] is not None:
            serialized = serialize_theme_colors_update(data["theme_colors"])
            existing = merge_theme_colors(
                row.storefront_template or "sports",
                row.theme_colors or {},
            )
            existing.update(serialized)
            data["theme_colors"] = existing
        if "payment_gateway_provider" in data and data["payment_gateway_provider"] is not None:
            data["payment_gateway_provider"] = data["payment_gateway_provider"].strip().lower()
        if "payment_gateway_merchant_id" in data and data["payment_gateway_merchant_id"] is not None:
            data["payment_gateway_merchant_id"] = data["payment_gateway_merchant_id"].strip()
        if "payment_gateway_environment" in data and data["payment_gateway_environment"] is not None:
            env = data["payment_gateway_environment"].strip().lower()
            if env not in ALLOWED_PAYMENT_GATEWAY_ENVIRONMENTS:
                raise ConflictError(f"Ambiente de pasarela no válido: {env}")
            data["payment_gateway_environment"] = env
        if "payment_gateway_enabled" in data and data["payment_gateway_enabled"] is not None:
            data["payment_gateway_enabled"] = bool(data["payment_gateway_enabled"])
        if "payment_gateway_api_key" in data:
            api_key = (data.pop("payment_gateway_api_key") or "").strip()
            if api_key:
                row.payment_gateway_api_key = api_key
        if "billing_country" in data and data["billing_country"] is not None:
            country = data["billing_country"].strip().upper()
            if country not in ALLOWED_BILLING_COUNTRIES:
                raise ConflictError(f"País de facturación no válido: {country}")
            data["billing_country"] = country
        if "billing_provider" in data and data["billing_provider"] is not None:
            data["billing_provider"] = data["billing_provider"].strip().lower()
        if "billing_enabled" in data and data["billing_enabled"] is not None:
            data["billing_enabled"] = bool(data["billing_enabled"])
        if "billing_api_key" in data:
            billing_key = (data.pop("billing_api_key") or "").strip()
            if billing_key:
                row.billing_api_key = billing_key
        if "billing_username" in data and data["billing_username"] is not None:
            data["billing_username"] = data["billing_username"].strip()
        if "billing_branch" in data and data["billing_branch"] is not None:
            data["billing_branch"] = data["billing_branch"].strip() or "Casa Matriz"
        if "billing_emitter_rut" in data and data["billing_emitter_rut"] is not None:
            data["billing_emitter_rut"] = data["billing_emitter_rut"].strip()
        for field in (
            "billing_emitter_name",
            "billing_emitter_activity",
            "billing_emitter_address",
            "billing_emitter_commune",
            "billing_emitter_city",
        ):
            if field in data and data[field] is not None:
                data[field] = data[field].strip()

        for field, value in data.items():
            setattr(row, field, value)

        self.commit()
        self.db.refresh(row)
        return _to_out(row)
