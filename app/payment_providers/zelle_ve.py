"""Zelle no tiene API de comercio. Sandbox confirma el pago en local; producción queda pendiente de revisión."""

from __future__ import annotations

from app.payment_providers.base import (
    PaymentCommitResult,
    PaymentGatewayConfig,
    PaymentSessionResult,
)


class ZelleVeProvider:
    provider_id = "zelle_ve"

    def resolve_config(
        self,
        enabled: bool,
        merchant_id: str,
        api_key: str,
        environment: str,
        api_secret: str = "",
        currency: str = "",
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
            base_url="",
            api_secret=api_secret,
            currency=currency,
        )

    def init_session(
        self,
        config: PaymentGatewayConfig,
        buy_order: str,
        session_id: str,
        amount: int,
        return_url: str,
    ) -> PaymentSessionResult:
        del session_id, amount, return_url
        kind = "sandbox" if config.environment == "sandbox" else "manual"
        return PaymentSessionResult(
            token=f"{kind}:{self.provider_id}:{buy_order}",
            redirect_url="",
        )

    def commit_session(self, config: PaymentGatewayConfig, token: str) -> PaymentCommitResult:
        sandbox = token.startswith(f"sandbox:{self.provider_id}:") and config.environment == "sandbox"
        buy_order = token.split(":", 2)[2] if token.count(":") >= 2 else ""
        return PaymentCommitResult(
            success=sandbox,
            response_code=0 if sandbox else -1,
            status="AUTHORIZED" if sandbox else "MANUAL",
            buy_order=buy_order,
            session_id="",
            amount=0,
            authorization_code=token if sandbox else "",
            token=token,
        )
