"""Resolución de credenciales de pasarela desde store_settings."""

from __future__ import annotations

from app.models.store_settings import StoreSettings
from app.payment_providers.base import PaymentGatewayConfig
from app.payment_providers.registry import get_payment_provider


def resolve_payment_gateway_config(row: StoreSettings) -> PaymentGatewayConfig | None:
    provider_id = (row.payment_gateway_provider or "").strip().lower()
    if not provider_id:
        return None

    provider = get_payment_provider(provider_id)
    if provider is None:
        return None

    if hasattr(provider, "resolve_config"):
        return provider.resolve_config(
            bool(row.payment_gateway_enabled),
            row.payment_gateway_merchant_id or "",
            row.payment_gateway_api_key or "",
            row.payment_gateway_environment or "sandbox",
        )

    return None
