"""Registro de proveedores de pasarela por país / mercado."""

from __future__ import annotations

from app.payment_providers.base import PaymentGatewayProvider
from app.payment_providers.transbank_cl import TransbankClProvider

_PROVIDERS: dict[str, PaymentGatewayProvider] = {
    TransbankClProvider.provider_id: TransbankClProvider(),
}

_PROVIDER_META: dict[str, dict[str, str]] = {
    "transbank_cl": {
        "label": "Transbank (Chile)",
        "country": "CL",
    },
}


def get_payment_provider(provider_id: str) -> PaymentGatewayProvider | None:
    return _PROVIDERS.get((provider_id or "").strip().lower())


def list_payment_providers() -> list[dict[str, str]]:
    return [
        {"id": provider_id, **meta}
        for provider_id, meta in _PROVIDER_META.items()
    ]


def get_provider_label(provider_id: str) -> str:
    meta = _PROVIDER_META.get((provider_id or "").strip().lower())
    return meta["label"] if meta else provider_id
