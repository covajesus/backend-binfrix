"""Orquestación de pasarelas de pago (multi-proveedor / multi-país)."""

from __future__ import annotations

from dataclasses import replace

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import AppError, NotFoundError
from app.models.payment import Payment
from app.payment_providers.registry import get_payment_provider, get_provider_label
from app.payments.catalog import merge_payment_methods
from app.schemas.payment import PaymentCreate
from app.schemas.payment_session import PaymentSandboxCompleteOut, PaymentSessionInitOut
from app.services.base import BaseService
from app.services.order_service import OrderRepository
from app.services.payment_service import PaymentRepository, PaymentService
from app.services.store_settings_service import StoreSettingsRepository, StoreSettingsService
from app.utils.payment_gateway import resolve_method_gateway, resolve_payment_gateway_config
from app.utils.payments import generate_payment_number, today


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

    def _provider_return_url(self, tenant_slug: str, provider_id: str, buy_order: str) -> str:
        shared = self._return_url(tenant_slug)
        root = shared.rsplit("/return", 1)[0]
        if provider_id == "binance_ve":
            return f"{root}/binance/return/{buy_order}"
        if provider_id == "payu_co":
            return f"{root}/payu/return"
        if provider_id == "wompi_co":
            return f"{root}/wompi/return"
        return shared

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
        method: str = "",
    ) -> PaymentSessionInitOut:
        order_repo = self._order_repo(tenant_id)
        payment_repo = self._payment_repo(tenant_id)

        order = order_repo.get_by_id(order_id)
        if order.payment_status == "paid":
            raise AppError("El pedido ya fue pagado", 400)

        settings_row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        config = resolve_method_gateway(settings_row, method or "webpay")
        if config is None:
            raise AppError("Ese medio de pago no está activo o no es una pasarela", 400)
        if order.customer_email:
            config = replace(config, payer_email=order.customer_email)
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
            return_url=self._provider_return_url(tenant_slug, config.provider_id, buy_order),
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
                created_at=today(),
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

    def complete_sandbox(self, tenant_id: str, token: str) -> PaymentSandboxCompleteOut:
        raw = token.strip()
        if not raw.startswith("sandbox:") or raw.count(":") < 2:
            raise AppError("Token de sandbox inválido", 400)

        _, provider_id, buy_order = raw.split(":", 2)
        settings_row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        method = {
            "zelle_ve": "zelle",
            "binance_ve": "binance",
            "wompi_co": "wompi",
        }.get(provider_id, "")
        config = resolve_method_gateway(settings_row, method) if method else None
        if config is None or config.environment != "sandbox" or config.provider_id != provider_id:
            raise AppError("Sandbox no está activo para este medio de pago", 400)

        order_repo = self._order_repo(tenant_id)
        payment_repo = self._payment_repo(tenant_id)
        payment = payment_repo.find_by_transaction_ref(raw)
        order = order_repo.find_by_order_number(buy_order)
        if order is None and payment is not None:
            try:
                order = order_repo.get_by_id(payment.order_id)
            except NotFoundError:
                order = None
        if order is None:
            raise AppError("No se encontró el pedido del pago sandbox", 404)

        provider_label = get_provider_label(provider_id)
        if payment is None:
            payment = payment_repo.find_latest_for_order(order.id)
        if payment is not None:
            payment.status = "completed"
            payment.transaction_ref = raw
            payment.method = provider_id
            payment.notes = f"Pago {provider_label} sandbox"
        order.payment_status = "paid"
        order.status = "processing"
        self.commit()
        return PaymentSandboxCompleteOut(status="paid", order_number=order.order_number)

    def confirm_mobile_payment(
        self,
        tenant_id: str,
        order_id: str,
        reference: str,
    ) -> PaymentSandboxCompleteOut:
        ref = reference.strip()
        if not ref:
            raise AppError("Ingresa la referencia del Pago móvil", 400)

        settings_row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        block = merge_payment_methods(settings_row.payment_methods)["VE"]["pago_movil"]
        if not block.get("enabled"):
            raise AppError("Pago móvil no está activo", 400)

        order = self._order_repo(tenant_id).get_by_id(order_id)
        if order.payment_status == "paid":
            raise AppError("El pedido ya fue pagado", 400)

        sandbox = (block.get("environment") or "sandbox") == "sandbox"
        if sandbox and ref != "123456":
            raise AppError("En sandbox la referencia de prueba es 123456", 400)

        payment_repo = self._payment_repo(tenant_id)
        payment = payment_repo.find_latest_for_order(order.id)
        note = f"Pago móvil ref {ref}"
        if payment is None:
            payment = Payment(
                tenant_id=tenant_id,
                payment_number=generate_payment_number(payment_repo.count_all()),
                order_id=order.id,
                order_number=order.order_number,
                customer_name=order.customer_name,
                amount=int(order.total or 0),
                method="pago_movil",
                status="pending",
                transaction_ref=ref[:120],
                notes=note,
                created_at=today(),
            )
            payment_repo.add(payment)
        else:
            payment.method = "pago_movil"
            payment.transaction_ref = ref[:120]
            payment.notes = note

        if sandbox:
            payment.status = "completed"
            order.payment_status = "paid"
            order.status = "processing"
            result = "paid"
        else:
            payment.status = "pending"
            order.payment_status = "pending"
            result = "pending"

        current = (order.notes or "").strip()
        if note not in current:
            order.notes = f"{current} | {note}".strip(" |")
        self.commit()
        return PaymentSandboxCompleteOut(status=result, order_number=order.order_number)

    def _record_gateway_result(self, tenant_id: str, order, commit, provider_id: str) -> str:
        label = get_provider_label(provider_id)
        payment = self._payment_repo(tenant_id).find_latest_for_order(order.id)
        if commit.success:
            auth = (commit.authorization_code or commit.token or "")[:120]
            if payment is not None:
                payment.status = "completed"
                payment.transaction_ref = auth
                payment.method = provider_id
                payment.notes = f"Pago {label} autorizado"
            else:
                PaymentService(self.db, tenant_id=tenant_id).create_payment(
                    PaymentCreate(
                        order_id=order.id,
                        order_number=order.order_number,
                        customer_name=order.customer_name,
                        amount=commit.amount or int(order.total or 0),
                        method=provider_id,
                        status="completed",
                        transaction_ref=auth,
                        notes=f"Pago {label} autorizado",
                    )
                )
            order.payment_status = "paid"
            order.status = "processing"
            self.commit()
            return self._frontend_result_url(tenant_id, f"status=success&order={order.order_number}")

        if commit.status == "PENDING":
            if payment is not None:
                payment.status = "pending"
                payment.notes = f"Pago {label} pendiente de confirmación"
            order.payment_status = "pending"
            self.commit()
            return self._frontend_result_url(tenant_id, f"status=pending&order={order.order_number}")

        if payment is not None:
            payment.status = "failed"
            payment.notes = f"{label} no autorizado ({commit.status})"
        order.payment_status = "pending"
        self.commit()
        return self._frontend_result_url(
            tenant_id,
            f"status=error&reason=declined&order={order.order_number}",
        )

    def complete_binance_return(self, tenant_id: str, ref: str) -> str:
        buy_order = (ref or "").strip()
        order = self._order_repo(tenant_id).find_by_order_number(buy_order) if buy_order else None
        if order is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=order")

        settings_row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        config = resolve_method_gateway(settings_row, "binance")
        if config is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=declined")

        payment = self._payment_repo(tenant_id).find_latest_for_order(order.id)
        token = (payment.transaction_ref if payment is not None else "") or buy_order
        try:
            commit = self._provider("binance_ve").commit_session(config, token)
        except AppError:
            return self._frontend_result_url(tenant_id, "status=error&reason=connection")
        return self._record_gateway_result(tenant_id, order, commit, "binance_ve")

    def complete_payu_return(self, tenant_id: str, params: dict) -> str:
        settings_row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        config = resolve_method_gateway(settings_row, "payu")
        if config is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=declined")
        try:
            commit = self._provider("payu_co").commit_response(config, params)
        except AppError:
            return self._frontend_result_url(tenant_id, "status=error&reason=declined")
        order = self._order_repo(tenant_id).find_by_order_number(commit.buy_order)
        if order is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=order")
        return self._record_gateway_result(tenant_id, order, commit, "payu_co")

    def complete_wompi_return(self, tenant_id: str, transaction_id: str) -> str:
        token = (transaction_id or "").strip()
        if not token:
            return self._frontend_result_url(tenant_id, "status=error&reason=declined")
        settings_row = self._settings_repo(tenant_id).require_row(
            "Pasarela de pago no configurada para esta tienda",
        )
        config = resolve_method_gateway(settings_row, "wompi")
        if config is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=declined")
        try:
            commit = self._provider("wompi_co").commit_session(config, token)
        except AppError:
            return self._frontend_result_url(tenant_id, "status=error&reason=connection")
        order = self._order_repo(tenant_id).find_by_order_number(commit.buy_order)
        if order is None:
            return self._frontend_result_url(tenant_id, "status=error&reason=order")
        return self._record_gateway_result(tenant_id, order, commit, "wompi_co")

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
