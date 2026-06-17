"""Contrato común para proveedores de facturación electrónica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BillingProviderConfig:
    provider_id: str
    base_url: str
    email: str
    password: str
    branch_name: str
    emitter_rut: str
    emitter_name: str
    emitter_activity: str
    emitter_address: str
    emitter_commune: str
    emitter_city: str
    emitter_email: str


@dataclass(frozen=True)
class BillingIssueResult:
    dte_type: int
    folio: int
    emisor_rut: str
    receptor_rut: str
    total: float
    fecha_emision: str


class BillingProvider(Protocol):
    provider_id: str

    def issue_boleta(
        self,
        config: BillingProviderConfig,
        order_payload: dict,
    ) -> BillingIssueResult: ...

    def issue_factura(
        self,
        config: BillingProviderConfig,
        order_payload: dict,
        receptor: dict,
    ) -> BillingIssueResult: ...

    def fetch_pdf(
        self,
        config: BillingProviderConfig,
        emisor_rut: str,
        dte_type: int,
        folio: int,
    ) -> bytes: ...
