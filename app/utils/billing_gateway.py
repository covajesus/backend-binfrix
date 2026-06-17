"""Resolución de credenciales de facturación desde store_settings."""

from __future__ import annotations

from app.models.store_settings import StoreSettings
from app.models.tenant import Tenant
from app.billing_providers.base import BillingProviderConfig
from app.billing_providers.registry import get_billing_provider


def resolve_billing_config(row: StoreSettings, tenant: Tenant | None = None) -> BillingProviderConfig | None:
    provider_id = (row.billing_provider or "").strip().lower()
    if not provider_id:
        return None

    provider = get_billing_provider(provider_id)
    if provider is None or not hasattr(provider, "resolve_config"):
        return None

    tenant_name = tenant.name if tenant else "Tienda"
    return provider.resolve_config(
        bool(row.billing_enabled),
        row.billing_username or "",
        row.billing_api_key or "",
        row.billing_branch or "",
        row.billing_emitter_rut or "",
        row.billing_emitter_name or tenant_name,
        row.billing_emitter_activity or "",
        row.billing_emitter_address or "",
        row.billing_emitter_commune or "",
        row.billing_emitter_city or "",
        row.contact_email or row.billing_username or "",
    )
