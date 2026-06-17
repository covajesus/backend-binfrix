from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ALLOWED_SOCIAL_IDS = frozenset({"instagram", "facebook", "x", "youtube"})
ALLOWED_STOREFRONT_TEMPLATES = frozenset({"sports", "industrial-kitchen", "electronics"})
ALLOWED_LOCALES = frozenset({"es", "en"})
ALLOWED_PAYMENT_GATEWAY_ENVIRONMENTS = frozenset({"sandbox", "production"})
ALLOWED_BILLING_COUNTRIES = frozenset({"CL", "CO", "PE", "VE"})


class SocialLink(BaseModel):
    id: str = Field(min_length=1, max_length=30)
    label: str = Field(min_length=1, max_length=80)
    href: str = Field(min_length=1, max_length=500)
    show_in_header: bool = False
    show_in_footer: bool = False


class HeaderNavLink(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    href: str = Field(min_length=1, max_length=500)
    group: Literal["left", "right"] = "left"


class StoreSettingsUpdate(BaseModel):
    phone: str | None = None
    schedule: str | None = None
    support_label: str | None = None
    support_href: str | None = None
    contact_email: str | None = None
    store_url: str | None = None
    store_logo_url: str | None = None
    storefront_template: str | None = None
    multilingual_enabled: bool | None = None
    default_locale: str | None = None
    account_label: str | None = None
    account_href: str | None = None
    promo_messages: list[str] | None = None
    header_links: list[HeaderNavLink] | None = None
    social_links: list[SocialLink] | None = None
    theme_colors: dict[str, str] | None = None
    payment_gateway_enabled: bool | None = None
    payment_gateway_provider: str | None = None
    payment_gateway_merchant_id: str | None = None
    payment_gateway_api_key: str | None = None
    payment_gateway_environment: str | None = None
    billing_enabled: bool | None = None
    billing_country: str | None = None
    billing_provider: str | None = None
    billing_api_key: str | None = None
    billing_username: str | None = None
    billing_branch: str | None = None
    billing_emitter_rut: str | None = None
    billing_emitter_name: str | None = None
    billing_emitter_activity: str | None = None
    billing_emitter_address: str | None = None
    billing_emitter_commune: str | None = None
    billing_emitter_city: str | None = None


class StoreSettingsOut(BaseModel):
    phone: str
    phone_href: str
    schedule: str
    support_label: str
    support_href: str
    contact_email: str
    store_url: str
    store_logo_url: str
    storefront_template: str
    multilingual_enabled: bool
    default_locale: str
    account_label: str
    account_href: str
    promo_messages: list[str]
    header_links: list[HeaderNavLink]
    social_links: list[SocialLink]
    theme_colors: dict[str, str]
    payment_gateway_enabled: bool = False
    payment_gateway_provider: str = ""
    payment_gateway_merchant_id: str = ""
    payment_gateway_environment: str = "sandbox"
    payment_gateway_api_key_configured: bool = False
    billing_enabled: bool = False
    billing_country: str = "CL"
    billing_provider: str = ""
    billing_api_key_configured: bool = False
    billing_username: str = ""
    billing_branch: str = "Casa Matriz"
    billing_emitter_rut: str = ""
    billing_emitter_name: str = ""
    billing_emitter_activity: str = ""
    billing_emitter_address: str = ""
    billing_emitter_commune: str = ""
    billing_emitter_city: str = ""
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StoreSettingsPublicOut(BaseModel):
    phone: str
    phone_href: str
    schedule: str
    support_label: str
    support_href: str
    contact_email: str
    store_url: str
    store_logo_url: str
    storefront_template: str
    multilingual_enabled: bool
    default_locale: str
    account_label: str
    account_href: str
    promo_messages: list[str]
    header_links: list[HeaderNavLink]
    social_links: list[SocialLink]
    theme_colors: dict[str, str]
    payment_gateway_enabled: bool = False
    payment_gateway_provider: str = ""
