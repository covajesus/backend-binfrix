"""Proveedor Transbank Webpay Plus (Chile) — implementación REST."""

from __future__ import annotations

import httpx

from app.core.exceptions import AppError
from app.payment_providers.base import (
    PaymentCommitResult,
    PaymentGatewayConfig,
    PaymentSessionResult,
)

INTEGRATION_COMMERCE_CODE = "597055555532"
INTEGRATION_API_KEY = "579B532A7440BB0C9079DED326365461CD0946DC9F9C4C6C2B8F6C5D8A3A9E3B"

BASE_URLS = {
    "sandbox": "https://webpay3gint.transbank.cl",
    "production": "https://webpay3g.transbank.cl",
}


class TransbankClProvider:
    provider_id = "transbank_cl"

    def resolve_config(
        self,
        enabled: bool,
        merchant_id: str,
        api_key: str,
        environment: str,
    ) -> PaymentGatewayConfig | None:
        if not enabled:
            return None

        env = (environment or "sandbox").strip().lower()
        if env not in BASE_URLS:
            env = "sandbox"

        merchant = (merchant_id or "").strip()
        secret = (api_key or "").strip()

        if env == "sandbox" and not merchant and not secret:
            merchant = INTEGRATION_COMMERCE_CODE
            secret = INTEGRATION_API_KEY
        elif not merchant or not secret:
            return None

        return PaymentGatewayConfig(
            provider_id=self.provider_id,
            merchant_id=merchant,
            api_key=secret,
            environment=env,
            base_url=BASE_URLS[env],
        )

    def _headers(self, config: PaymentGatewayConfig) -> dict[str, str]:
        return {
            "Tbk-Api-Key-Id": config.merchant_id,
            "Tbk-Api-Key-Secret": config.api_key,
            "Content-Type": "application/json",
        }

    def init_session(
        self,
        config: PaymentGatewayConfig,
        buy_order: str,
        session_id: str,
        amount: int,
        return_url: str,
    ) -> PaymentSessionResult:
        payload = {
            "buy_order": buy_order,
            "session_id": session_id,
            "amount": amount,
            "return_url": return_url,
        }
        url = f"{config.base_url}/rswebpaytransaction/api/webpay/v1.2/transactions"
        try:
            response = httpx.post(url, json=payload, headers=self._headers(config), timeout=30.0)
        except httpx.HTTPError as exc:
            raise AppError(f"No se pudo conectar con la pasarela de pago: {exc}", 502) from exc

        if response.status_code >= 400:
            detail = response.text[:300] if response.text else "Error desconocido"
            raise AppError(f"La pasarela rechazó la transacción: {detail}", 400)

        data = response.json()
        token = str(data.get("token") or "").strip()
        redirect_url = str(data.get("url") or "").strip()
        if not token or not redirect_url:
            raise AppError("Respuesta inválida de la pasarela de pago", 502)

        return PaymentSessionResult(token=token, redirect_url=redirect_url)

    def commit_session(
        self,
        config: PaymentGatewayConfig,
        token: str,
    ) -> PaymentCommitResult:
        url = f"{config.base_url}/rswebpaytransaction/api/webpay/v1.2/transactions/{token}"
        try:
            response = httpx.put(url, headers=self._headers(config), timeout=30.0)
        except httpx.HTTPError:
            return PaymentCommitResult(
                success=False,
                response_code=-1,
                status="CONNECTION_ERROR",
                buy_order="",
                session_id="",
                amount=0,
                authorization_code="",
                token=token,
            )

        if response.status_code >= 400:
            return PaymentCommitResult(
                success=False,
                response_code=-1,
                status="HTTP_ERROR",
                buy_order="",
                session_id="",
                amount=0,
                authorization_code="",
                token=token,
            )

        data = response.json()
        response_code = int(data.get("response_code", -1))
        status = str(data.get("status") or "").upper()
        return PaymentCommitResult(
            success=response_code == 0 and status == "AUTHORIZED",
            response_code=response_code,
            status=status,
            buy_order=str(data.get("buy_order") or ""),
            session_id=str(data.get("session_id") or ""),
            amount=int(data.get("amount") or 0),
            authorization_code=str(data.get("authorization_code") or ""),
            token=token,
        )
