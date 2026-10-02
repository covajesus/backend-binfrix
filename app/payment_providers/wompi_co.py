"""Wompi Web Checkout (Colombia): tarjeta, PSE y Nequi."""

from __future__ import annotations

import hashlib
from urllib.parse import urlencode

import httpx

from app.core.exceptions import AppError
from app.payment_providers.base import (
    PaymentCommitResult,
    PaymentGatewayConfig,
    PaymentSessionResult,
)

CHECKOUT_URL = "https://checkout.wompi.co/p/"
HOSTS = {
    "sandbox": "https://sandbox.wompi.co/v1",
    "production": "https://production.wompi.co/v1",
}


class WompiCoProvider:
    provider_id = "wompi_co"

    def resolve_config(
        self,
        enabled: bool,
        merchant_id: str,
        api_key: str,
        environment: str,
        api_secret: str = "",
        currency: str = "COP",
        private_key: str = "",
    ) -> PaymentGatewayConfig | None:
        del merchant_id
        if not enabled:
            return None
        env = (environment or "sandbox").strip().lower()
        if env not in HOSTS:
            env = "sandbox"
        return PaymentGatewayConfig(
            provider_id=self.provider_id,
            merchant_id="",
            api_key=(api_key or "").strip(),
            environment=env,
            base_url=HOSTS[env],
            api_secret=(api_secret or "").strip(),
            currency=(currency or "COP").upper(),
            private_key=(private_key or "").strip(),
        )

    def uses_local_sandbox(self, config: PaymentGatewayConfig) -> bool:
        return config.environment == "sandbox" and (
            not config.api_key or not config.api_secret or not config.private_key
        )

    def init_session(
        self,
        config: PaymentGatewayConfig,
        buy_order: str,
        session_id: str,
        amount: int,
        return_url: str,
    ) -> PaymentSessionResult:
        del session_id
        if self.uses_local_sandbox(config):
            return PaymentSessionResult(
                token=f"sandbox:{self.provider_id}:{buy_order}",
                redirect_url="",
            )
        if not config.api_key or not config.api_secret or not config.private_key:
            raise AppError(
                "Wompi requiere llave pública, llave privada y secreto de integridad",
                400,
            )
        cents = int(amount) * 100
        currency = config.currency or "COP"
        raw = f"{buy_order}{cents}{currency}{config.api_secret}"
        signature = hashlib.sha256(raw.encode()).hexdigest()
        params = {
            "public-key": config.api_key,
            "currency": currency,
            "amount-in-cents": str(cents),
            "reference": buy_order,
            "signature:integrity": signature,
            "redirect-url": return_url,
        }
        return PaymentSessionResult(
            token=buy_order,
            redirect_url=f"{CHECKOUT_URL}?{urlencode(params)}",
        )

    def commit_session(self, config: PaymentGatewayConfig, token: str) -> PaymentCommitResult:
        sandbox = token.startswith(f"sandbox:{self.provider_id}:") and self.uses_local_sandbox(config)
        buy_order = token.split(":", 2)[2] if token.count(":") >= 2 else token
        if sandbox:
            return PaymentCommitResult(
                success=True,
                response_code=0,
                status="AUTHORIZED",
                buy_order=buy_order,
                session_id="",
                amount=0,
                authorization_code=token,
                token=token,
            )
        if not config.private_key or not token:
            return PaymentCommitResult(
                success=False,
                response_code=-1,
                status="PENDING",
                buy_order=buy_order,
                session_id="",
                amount=0,
                authorization_code="",
                token=token,
            )
        url = f"{config.base_url}/transactions/{token}"
        try:
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {config.private_key}"},
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AppError(f"No se pudo consultar Wompi: {exc}", 502) from exc
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            detail = str((data.get("error") or {}).get("reason") or response.text[:300])
            raise AppError(f"Wompi rechazó la consulta: {detail}", 400)
        payload = data.get("data") or {}
        status = str(payload.get("status") or "").upper()
        approved = status == "APPROVED"
        pending = status in {"PENDING", ""}
        return PaymentCommitResult(
            success=approved,
            response_code=0 if approved else -1,
            status="AUTHORIZED" if approved else ("PENDING" if pending else status or "DECLINED"),
            buy_order=str(payload.get("reference") or buy_order),
            session_id="",
            amount=int((payload.get("amount_in_cents") or 0) / 100),
            authorization_code=str(payload.get("id") or token) if approved else "",
            token=token,
        )
