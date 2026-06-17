"""Orquestación de pasarelas de pago (multi-proveedor / multi-país)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import AppError, NotFoundError
from app.models.payment import Payment
from app.payment_providers.registry import get_payment_provider, get_provider_label
from app.schemas.payment import PaymentCreate
from app.schemas.payment_session import PaymentSessionInitOut
from app.services.base import BaseService
from app.services.order_service import OrderRepository
from app.services.payment_service import PaymentRepository, PaymentService
from app.services.store_settings_service import StoreSettingsRepository, StoreSettingsService
from app.utils.payment_gateway import resolve_payment_gateway_config
from app.utils.payments import generate_payment_number


class PaymentGatewayService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.settings = get_settings()

    def _order_repo(self, tenant_id: str) -> OrderRepository:
        return OrderRepository(self.db, tenant_id=tenant_id)

    def _payment_repo(self, tenant_id: str) -> PaymentRepository:
        return PaymentRepository(self.db, tenant_id=tenant_id)

    def _settings_repo(self, tenant_id: str) -> StoreSettingsRepository:
        return StoreSettingsRepository(self.db, tenant_id=tenant_id)

    def _gateway_config(self, tenant_id: str):
        row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        config = resolve_payment_gateway_config(row)
        if config is None:
            raise AppError("La pasarela de pago no está configurada correctamente", 400)
        return config, row

    def _provider(self, provider_id: str):
        provider = get_payment_provider(provider_id)
        if provider is None:
            raise AppError("Proveedor de pago no soportado", 400)
        return provider

    def _return_url(self, tenant_slug: str) -> str:
        base = self.settings.api_public_url.rstrip("/")
        prefix = self.settings.api_prefix.rstrip("/")
        return f"{base}{prefix}/store/{tenant_slug}/payments/return"

    def _frontend_result_url(self, tenant_id: str, query: str) -> str:
        settings = StoreSettingsService(self.db, tenant_id=tenant_id).get_settings()
        store_url = (settings.store_url or "").strip().rstrip("/")
        if not store_url:
            store_url = self.settings.ecommerce_public_url.rstrip("/")
        return f"{store_url}/checkout/result?{query}"

    def init_session(
        self,
        tenant_slug: str,
        tenant_id: str,
        order_id: str,
    ) -> PaymentSessionInitOut:
        order_repo = self._order_repo(tenant_id)
        payment_repo = self._payment_repo(tenant_id)

        order = order_repo.get_by_id(order_id)
        if order.payment_status == "paid":
            raise AppError("El pedido ya fue pagado", 400)

        config, _ = self._gateway_config(tenant_id)
        provider = self._provider(config.provider_id)

        amount = int(order.total or 0)
        if amount <= 0:
            raise AppError("El total del pedido debe ser mayor a cero", 400)

        buy_order = order.order_number[:26]
        session_id = order.id[:61]
        result = provider.init_session(
            config,
            buy_order=buy_order,
            session_id=session_id,
            amount=amount,
            return_url=self._return_url(tenant_slug),
        )

        provider_label = get_provider_label(config.provider_id)
        existing_payment = payment_repo.find_latest_for_order(order.id)
        if existing_payment is None:
            count = payment_repo.count_all()
            payment = Payment(
                tenant_id=tenant_id,
                payment_number=generate_payment_number(count),
                order_id=order.id,
                order_number=order.order_number,
                customer_name=order.customer_name,
                amount=amount,
                method=config.provider_id,
                status="pending",
                transaction_ref=result.token,
                notes=f"Pago {provider_label} iniciado",
            )
            payment_repo.add(payment)
        else:
            existing_payment.transaction_ref = result.token
            existing_payment.status = "pending"
            existing_payment.amount = amount
            existing_payment.method = config.provider_id

        order.payment_status = "pending"
        order.notes = (order.notes or "").strip()
        pending_note = f"{provider_label} pendiente"
        if pending_note not in order.notes:
            order.notes = f"{order.notes} | {pending_note}".strip(" |")

        self.commit()

        return PaymentSessionInitOut(
            token=result.token,
            url=result.redirect_url,
            order_id=order.id,
            order_number=order.order_number,
        )

    def complete_session(self, tenant_id: str, token_ws: str) -> str:
        token = token_ws.strip()
        if not token:
            raise AppError("Token de pago no recibido", 400)

        order_repo = self._order_repo(tenant_id)
        payment_repo = self._payment_repo(tenant_id)

        config, _ = self._gateway_config(tenant_id)
        provider = self._provider(config.provider_id)
        provider_label = get_provider_label(config.provider_id)

        commit = provider.commit_session(config, token)

        if commit.status == "CONNECTION_ERROR":
            return self._frontend_result_url(tenant_id, "status=error&reason=connection")

        if commit.status == "HTTP_ERROR":
            return self._frontend_result_url(tenant_id, "status=error&reason=declined")

        order = order_repo.find_by_order_number(commit.buy_order)
        if order is None and commit.session_id:
            try:
                order = order_repo.get_by_id(commit.session_id)
            except NotFoundError:
                order = None

        if order is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=order")

        payment = payment_repo.find_latest_for_order(order.id)

        if commit.success:
            auth_code = commit.authorization_code or token
            if payment is not None:
                payment.status = "completed"
                payment.transaction_ref = auth_code
                payment.notes = f"Pago {provider_label} autorizado"
            else:
                PaymentService(self.db, tenant_id=tenant_id).create_payment(
                    PaymentCreate(
                        order_id=order.id,
                        order_number=order.order_number,
                        customer_name=order.customer_name,
                        amount=commit.amount or int(order.total or 0),
                        method=config.provider_id,
                        status="completed",
                        transaction_ref=auth_code,
                        notes=f"Pago {provider_label} autorizado",
                    )
                )

            order.payment_status = "paid"
            order.status = "processing"
            self.commit()
            return self._frontend_result_url(
                tenant_id,
                f"status=success&order={order.order_number}",
            )

        if payment is not None:
            payment.status = "failed"
            payment.notes = f"{provider_label} no autorizado ({commit.status})"
        order.payment_status = "pending"
        self.commit()
        return self._frontend_result_url(
            tenant_id,
            f"status=error&order={order.order_number}&reason=declined",
        )
