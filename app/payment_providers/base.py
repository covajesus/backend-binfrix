"""Contrato común para proveedores de pasarela de pago."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaymentGatewayConfig:
    provider_id: str
    merchant_id: str
    api_key: str
    environment: str
    base_url: str


@dataclass(frozen=True)
class PaymentSessionResult:
    token: str
    redirect_url: str


@dataclass(frozen=True)
class PaymentCommitResult:
    success: bool
    response_code: int
    status: str
    buy_order: str
    session_id: str
    amount: int
    authorization_code: str
    token: str


class PaymentGatewayProvider(Protocol):
    provider_id: str

    def init_session(
        self,
        config: PaymentGatewayConfig,
        buy_order: str,
        session_id: str,
        amount: int,
        return_url: str,
    ) -> PaymentSessionResult: ...

    def commit_session(
        self,
        config: PaymentGatewayConfig,
        token: str,
    ) -> PaymentCommitResult: ...
