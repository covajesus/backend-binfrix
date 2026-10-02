"""Resolución de credenciales de pasarela desde store_settings."""

from __future__ import annotations

from app.models.store_settings import StoreSettings
from app.payment_providers.base import PaymentGatewayConfig
from app.payment_providers.registry import get_payment_provider
from app.payments.catalog import merge_payment_methods

METHOD_PROVIDER = {
    "webpay": "transbank_cl",
    "zelle": "zelle_ve",
    "binance": "binance_ve",
    "payu": "payu_co",
    "wompi": "wompi_co",
}


def resolve_method_gateway(row: StoreSettings, method: str) -> PaymentGatewayConfig | None:
    """Arma la config del medio elegido. Sandbox no exige credenciales reales."""
    methods = merge_payment_methods(row.payment_methods)
    method_id = (method or "").strip().lower()
    provider_id = METHOD_PROVIDER.get(method_id)
    if not provider_id:
        return None
    provider = get_payment_provider(provider_id)
    if provider is None or not hasattr(provider, "resolve_config"):
        return None

    if method_id == "webpay":
        block = methods["CL"]["webpay"]
        if not block.get("enabled"):
            return None
        return provider.resolve_config(
            True,
            row.payment_gateway_merchant_id or "",
            row.payment_gateway_api_key or "",
            block.get("environment") or row.payment_gateway_environment or "sandbox",
        )

    if method_id == "zelle":
        block = methods["VE"]["zelle"]
        return provider.resolve_config(
            bool(block.get("enabled")),
            block.get("email") or "",
            block.get("phone") or "",
            block.get("environment") or "sandbox",
        )

    block = methods["VE"]["binance"]
    if method_id == "binance":
        return provider.resolve_config(
            bool(block.get("enabled")),
            block.get("merchant_id") or "",
            block.get("api_key") or "",
            block.get("environment") or "sandbox",
            api_secret=block.get("api_secret") or "",
            currency=block.get("currency") or "USDT",
        )

    if method_id == "payu":
        block = methods["CO"]["payu"]
        return provider.resolve_config(
            bool(block.get("enabled")),
            block.get("merchant_id") or "",
            block.get("api_key") or "",
            block.get("environment") or "sandbox",
            api_secret=block.get("account_id") or "",
            currency="COP",
        )

    block = methods["CO"]["wompi"]
    return provider.resolve_config(
        bool(block.get("enabled")),
        "",
        block.get("public_key") or "",
        block.get("environment") or "sandbox",
        api_secret=block.get("integrity") or "",
        currency="COP",
        private_key=block.get("private_key") or "",
    )


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
