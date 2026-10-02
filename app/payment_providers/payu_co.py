"""PayU Latam WebCheckout (Colombia). Sandbox usa el comercio público de integración."""

from __future__ import annotations

import hashlib
from urllib.parse import urlencode

from app.core.exceptions import AppError
from app.payment_providers.base import (
    PaymentCommitResult,
    PaymentGatewayConfig,
    PaymentSessionResult,
)

SANDBOX_MERCHANT_ID = "508029"
SANDBOX_ACCOUNT_ID = "512321"
SANDBOX_API_KEY = "4Vj8eK4rloUd272L48hsrarnUA"
SANDBOX_URL = "https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu/"
PRODUCTION_URL = "https://checkout.payulatam.com/ppp-web-gateway-payu/"


class PayuCoProvider:
    provider_id = "payu_co"

    def resolve_config(
        self,
        enabled: bool,
        merchant_id: str,
        api_key: str,
        environment: str,
        api_secret: str = "",
        currency: str = "COP",
        payer_email: str = "",
    ) -> PaymentGatewayConfig | None:
        if not enabled:
            return None
        env = (environment or "sandbox").strip().lower()
        if env not in ("sandbox", "production"):
            env = "sandbox"
        merchant = (merchant_id or "").strip()
        account = (api_secret or "").strip()
        secret = (api_key or "").strip()
        if env == "sandbox" and not merchant and not account and not secret:
            merchant = SANDBOX_MERCHANT_ID
            account = SANDBOX_ACCOUNT_ID
            secret = SANDBOX_API_KEY
        elif not merchant or not account or not secret:
            return None
        return PaymentGatewayConfig(
            provider_id=self.provider_id,
            merchant_id=merchant,
            api_key=secret,
            environment=env,
            base_url=SANDBOX_URL if env == "sandbox" else PRODUCTION_URL,
            api_secret=account,
            currency=(currency or "COP").upper(),
            payer_email=(payer_email or "").strip(),
        )

    def signature(self, config: PaymentGatewayConfig, reference: str, amount: str) -> str:
        raw = "~".join(
            [config.api_key, config.merchant_id, reference, amount, config.currency or "COP"]
        )
        return hashlib.md5(raw.encode()).hexdigest()

    def response_signature(
        self,
        config: PaymentGatewayConfig,
        reference: str,
        amount: str,
        state: str,
    ) -> str:
        raw = "~".join(
            [config.api_key, config.merchant_id, reference, amount, config.currency or "COP", state]
        )
        return hashlib.md5(raw.encode()).hexdigest()

    def init_session(
        self,
        config: PaymentGatewayConfig,
        buy_order: str,
        session_id: str,
        amount: int,
        return_url: str,
    ) -> PaymentSessionResult:
        del session_id
        value = f"{int(amount)}.00"
        params = {
            "merchantId": config.merchant_id,
            "accountId": config.api_secret,
            "description": f"Pedido {buy_order}",
            "referenceCode": buy_order,
            "amount": value,
            "tax": "0",
            "taxReturnBase": "0",
            "currency": config.currency or "COP",
            "signature": self.signature(config, buy_order, value),
            "test": "1" if config.environment == "sandbox" else "0",
            "buyerEmail": config.payer_email or "pagos@binfrix.com",
            "responseUrl": return_url,
            "confirmationUrl": return_url,
        }
        return PaymentSessionResult(
            token=buy_order,
            redirect_url=f"{config.base_url}?{urlencode(params)}",
        )

    def commit_session(self, config: PaymentGatewayConfig, token: str) -> PaymentCommitResult:
        return PaymentCommitResult(
            success=False,
            response_code=-1,
            status="PENDING",
            buy_order=token,
            session_id="",
            amount=0,
            authorization_code="",
            token=token,
        )

    def commit_response(self, config: PaymentGatewayConfig, params: dict) -> PaymentCommitResult:
        reference = str(params.get("referenceCode") or params.get("reference_sale") or "").strip()
        state = str(params.get("transactionState") or params.get("state_pol") or "").strip()
        amount = str(params.get("TX_VALUE") or params.get("value") or "").strip()
        signature = str(params.get("signature") or params.get("sign") or "").strip().lower()
        if not reference or not state or not amount or not signature:
            raise AppError("Respuesta incompleta de PayU", 400)
        amounts = {amount}
        try:
            number = float(amount)
            amounts.add(f"{number:.1f}")
            amounts.add(f"{number:.2f}")
        except ValueError:
            pass
        if not any(signature == self.response_signature(config, reference, item, state) for item in amounts):
            raise AppError("Firma de PayU inválida", 400)
        approved = state == "4"
        pending = state == "7"
        return PaymentCommitResult(
            success=approved,
            response_code=0 if approved else -1,
            status="AUTHORIZED" if approved else ("PENDING" if pending else "DECLINED"),
            buy_order=reference,
            session_id="",
            amount=0,
            authorization_code=str(params.get("transactionId") or params.get("reference_pol") or ""),
            token=reference,
        )
