"""Binance Pay (Venezuela). Sandbox local si no hay credenciales; producción con API Binance Pay."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time

import httpx

from app.core.exceptions import AppError
from app.payment_providers.base import (
    PaymentCommitResult,
    PaymentGatewayConfig,
    PaymentSessionResult,
)

BINANCE_PAY_URL = "https://bpay.binanceapi.com/binancepay/openapi/v3/order"
BINANCE_QUERY_URL = "https://bpay.binanceapi.com/binancepay/openapi/v2/order/query"


class BinanceVeProvider:
    provider_id = "binance_ve"

    def resolve_config(
        self,
        enabled: bool,
        merchant_id: str,
        api_key: str,
        environment: str,
        api_secret: str = "",
        currency: str = "USDT",
    ) -> PaymentGatewayConfig | None:
        if not enabled:
            return None
        env = (environment or "sandbox").strip().lower()
        if env not in ("sandbox", "production"):
            env = "sandbox"
        return PaymentGatewayConfig(
            provider_id=self.provider_id,
            merchant_id=(merchant_id or "").strip(),
            api_key=(api_key or "").strip(),
            environment=env,
            base_url=BINANCE_PAY_URL,
            api_secret=(api_secret or "").strip(),
            currency=(currency or "USDT").upper(),
        )

    def uses_local_sandbox(self, config: PaymentGatewayConfig) -> bool:
        return config.environment == "sandbox"

    def init_session(
        self,
        config: PaymentGatewayConfig,
        buy_order: str,
        session_id: str,
        amount: int,
        return_url: str,
    ) -> PaymentSessionResult:
        if self.uses_local_sandbox(config):
            return PaymentSessionResult(
                token=f"sandbox:{self.provider_id}:{buy_order}",
                redirect_url="",
            )

        secret = config.api_secret
        if not config.merchant_id or not config.api_key or not secret:
            raise AppError(
                "Binance Pay en producción requiere merchant id, API key y API secret",
                400,
            )

        body = {
            "env": {"terminalType": "WEB"},
            "merchantTradeNo": buy_order[:32],
            "orderAmount": f"{amount:.2f}" if isinstance(amount, float) else f"{int(amount)}.00",
            "currency": (config.currency or "USDT").upper(),
            "goodsDetails": [
                {
                    "goodsType": "02",
                    "goodsCategory": "Z000",
                    "referenceGoodsId": session_id[:32] or "order",
                    "goodsName": f"Pedido {buy_order}"[:256],
                    "goodsDetail": "Binfrix checkout",
                }
            ],
            "returnUrl": return_url,
            "cancelUrl": return_url,
        }
        raw = json.dumps(body, separators=(",", ":"))
        timestamp = str(int(time.time() * 1000))
        nonce = secrets.token_hex(16)
        payload = f"{timestamp}\n{nonce}\n{raw}\n"
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha512).hexdigest().upper()
        headers = {
            "Content-Type": "application/json",
            "BinancePay-Timestamp": timestamp,
            "BinancePay-Nonce": nonce,
            "BinancePay-Certificate-SN": config.api_key,
            "BinancePay-Signature": signature,
        }
        try:
            response = httpx.post(config.base_url, content=raw, headers=headers, timeout=30.0)
        except httpx.HTTPError as exc:
            raise AppError(f"No se pudo conectar con Binance Pay: {exc}", 502) from exc

        data = response.json() if response.content else {}
        if response.status_code >= 400 or str(data.get("status")) not in ("SUCCESS", "success"):
            detail = str(data.get("errorMessage") or response.text[:300] or "Error desconocido")
            raise AppError(f"Binance Pay rechazó la orden: {detail}", 400)

        checkout = data.get("data") or {}
        token = str(checkout.get("prepayId") or "").strip()
        redirect_url = str(checkout.get("checkoutUrl") or checkout.get("deeplink") or "").strip()
        if not token or not redirect_url:
            raise AppError("Respuesta inválida de Binance Pay", 502)
        return PaymentSessionResult(token=token, redirect_url=redirect_url)

    def _signed_post(self, config: PaymentGatewayConfig, url: str, body: dict) -> dict:
        secret = config.api_secret
        raw = json.dumps(body, separators=(",", ":"))
        timestamp = str(int(time.time() * 1000))
        nonce = secrets.token_hex(16)
        payload = f"{timestamp}\n{nonce}\n{raw}\n"
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha512).hexdigest().upper()
        headers = {
            "Content-Type": "application/json",
            "BinancePay-Timestamp": timestamp,
            "BinancePay-Nonce": nonce,
            "BinancePay-Certificate-SN": config.api_key,
            "BinancePay-Signature": signature,
        }
        try:
            response = httpx.post(url, content=raw, headers=headers, timeout=30.0)
        except httpx.HTTPError as exc:
            raise AppError(f"No se pudo conectar con Binance Pay: {exc}", 502) from exc
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            detail = str(data.get("errorMessage") or response.text[:300] or "Error desconocido")
            raise AppError(f"Binance Pay rechazó la consulta: {detail}", 400)
        return data

    def commit_session(self, config: PaymentGatewayConfig, token: str) -> PaymentCommitResult:
        sandbox = token.startswith(f"sandbox:{self.provider_id}:") and config.environment == "sandbox"
        if sandbox:
            buy_order = token.split(":", 2)[2] if token.count(":") >= 2 else ""
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

        if not config.api_key or not config.api_secret:
            return PaymentCommitResult(
                success=False,
                response_code=-1,
                status="PENDING",
                buy_order="",
                session_id="",
                amount=0,
                authorization_code="",
                token=token,
            )

        trade_no = token.removeprefix("manual:")
        query = {"merchantTradeNo": trade_no} if trade_no.startswith("PED-") or token.startswith("manual:") else {"prepayId": token}
        data = self._signed_post(config, BINANCE_QUERY_URL, query)
        payload = data.get("data") or {}
        status = str(payload.get("status") or "").upper()
        buy_order = str(payload.get("merchantTradeNo") or "")
        paid = str(data.get("status") or "").upper() == "SUCCESS" and status == "PAY_SUCCESS"
        pending = status in {"", "INITIAL", "PENDING", "PAY_PENDING"}
        return PaymentCommitResult(
            success=paid,
            response_code=0 if paid else -1,
            status="AUTHORIZED" if paid else ("PENDING" if pending else status or "DECLINED"),
            buy_order=buy_order,
            session_id="",
            amount=0,
            authorization_code=str(payload.get("transactionId") or token) if paid else "",
            token=token,
        )
