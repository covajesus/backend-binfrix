"""Emisión de documentos tributarios (SimpleFactura y otros proveedores)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.billing_providers.registry import get_billing_provider
from app.core.exceptions import AppError
from app.models.order import Order
from app.schemas.billing import BillingDocumentOut, BillingIssueIn
from app.services.base import BaseService
from app.services.order_service import OrderRepository
from app.services.store_settings_service import StoreSettingsRepository
from app.services.tenant_service import TenantRepository
from app.utils.billing_gateway import resolve_billing_config


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_billing(billing: dict | None) -> BillingDocumentOut:
    raw = billing or {}
    return BillingDocumentOut(
        document_type=str(raw.get("document_type") or ""),
        dte_type=raw.get("dte_type"),
        folio=raw.get("folio"),
        status=str(raw.get("status") or ""),
        emisor_rut=str(raw.get("emisor_rut") or ""),
        receptor_rut=str(raw.get("receptor_rut") or ""),
        total=raw.get("total"),
        fecha_emision=str(raw.get("fecha_emision") or ""),
        error=str(raw.get("error") or ""),
        issued_at=raw.get("issued_at"),
    )


class BillingService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.tenant_id = tenant_id
        self.order_repo = OrderRepository(db, tenant_id=tenant_id)
        self.settings_repo = StoreSettingsRepository(db, tenant_id=tenant_id)
        self.tenant_repo = TenantRepository(db)

    def _order_payload(self, order: Order) -> dict:
        return {
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "shipping_address": order.shipping_address,
            "city": order.city,
            "total": order.total,
            "items": order.items or [],
        }

    def get_billing_status(self, order_id: str) -> BillingDocumentOut:
        order = self.order_repo.get_by_id(order_id)
        return _serialize_billing(order.billing if isinstance(order.billing, dict) else {})

    def issue_document(self, order_id: str, payload: BillingIssueIn) -> BillingDocumentOut:
        settings = self.settings_repo.require_row(
            "Facturación no configurada para esta tienda",
        )
        tenant = self.tenant_repo.get_by_id(self.tenant_id)
        config = resolve_billing_config(settings, tenant)
        if config is None:
            raise AppError(
                "Activa facturación y completa usuario, contraseña y RUT emisor en Facturación",
                400,
            )

        provider = get_billing_provider(config.provider_id)
        if provider is None:
            raise AppError("Proveedor de facturación no disponible", 400)

        order = self.order_repo.get_by_id(order_id)
        billing = order.billing if isinstance(order.billing, dict) else {}
        if billing.get("status") == "issued" and billing.get("folio"):
            raise AppError("Este pedido ya tiene un documento tributario emitido", 409)

        if order.payment_status != "paid":
            raise AppError("Solo se puede facturar pedidos con pago confirmado", 400)

        order_payload = self._order_payload(order)
        doc_type = payload.document_type.strip().lower()

        try:
            if doc_type == "boleta":
                result = provider.issue_boleta(config, order_payload)
            else:
                receptor = payload.receptor.model_dump() if payload.receptor else {}
                result = provider.issue_factura(config, order_payload, receptor)
        except AppError as exc:
            order.billing = {
                **billing,
                "document_type": doc_type,
                "status": "failed",
                "error": str(exc),
            }
            self.commit()
            raise

        issued = {
            "document_type": doc_type,
            "dte_type": result.dte_type,
            "folio": result.folio,
            "status": "issued",
            "emisor_rut": result.emisor_rut,
            "receptor_rut": result.receptor_rut,
            "total": result.total,
            "fecha_emision": result.fecha_emision,
            "error": "",
            "issued_at": utcnow().isoformat(),
        }
        order.billing = issued
        self.commit()
        return _serialize_billing(issued)

    def fetch_pdf(self, order_id: str) -> tuple[bytes, str]:
        settings = self.settings_repo.require_row("Facturación no configurada")
        tenant = self.tenant_repo.get_by_id(self.tenant_id)
        config = resolve_billing_config(settings, tenant)
        if config is None:
            raise AppError("Facturación no configurada", 400)

        provider = get_billing_provider(config.provider_id)
        if provider is None:
            raise AppError("Proveedor de facturación no disponible", 400)

        order = self.order_repo.get_by_id(order_id)
        billing = order.billing if isinstance(order.billing, dict) else {}
        if billing.get("status") != "issued" or not billing.get("folio"):
            raise AppError("Este pedido no tiene documento emitido", 400)

        pdf_bytes = provider.fetch_pdf(
            config,
            str(billing.get("emisor_rut") or config.emitter_rut),
            int(billing.get("dte_type") or 0),
            int(billing.get("folio") or 0),
        )
        doc_type = billing.get("document_type") or "documento"
        folio = billing.get("folio")
        filename = f"{doc_type}-{folio}.pdf"
        return pdf_bytes, filename
