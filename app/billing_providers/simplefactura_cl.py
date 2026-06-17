"""Proveedor SimpleFactura (Chile) — emisión boleta/factura vía API REST."""

from __future__ import annotations

from datetime import date

import httpx

from app.core.exceptions import AppError
from app.billing_providers.base import BillingIssueResult, BillingProviderConfig

BASE_URL = "https://api.simplefactura.cl"
DTE_BOLETA = 39
DTE_FACTURA = 33
CONSUMIDOR_FINAL_RUT = "66666666-6"


class SimpleFacturaClProvider:
    provider_id = "simplefactura_cl"

    def _token(self, config: BillingProviderConfig) -> str:
        url = f"{config.base_url}/token"
        payload = {"email": config.email, "password": config.password}
        try:
            response = httpx.post(url, json=payload, timeout=30.0)
        except httpx.HTTPError as exc:
            raise AppError(f"No se pudo conectar con SimpleFactura: {exc}", 502) from exc

        if response.status_code != 200:
            raise AppError(
                f"Credenciales SimpleFactura inválidas ({response.status_code})",
                400,
            )

        data = response.json()
        token = data.get("accessToken")
        if not token:
            raise AppError("SimpleFactura no devolvió accessToken", 502)
        return token

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _split_iva(self, total: int) -> tuple[int, int, int]:
        mnt_neto = round(total / 1.19)
        iva = total - mnt_neto
        return total, mnt_neto, iva

    def _build_detalle(self, items: list[dict]) -> list[dict]:
        detalle: list[dict] = []
        for index, item in enumerate(items, start=1):
            qty = int(item.get("quantity") or 0)
            price = int(item.get("unit_price") or 0)
            if qty <= 0:
                continue
            monto = qty * price
            detalle.append(
                {
                    "NroLinDet": index,
                    "NmbItem": str(item.get("product_title") or "Producto"),
                    "CdgItem": [],
                    "QtyItem": qty,
                    "UnmdItem": "un",
                    "PrcItem": price,
                    "MontoItem": monto,
                }
            )
        return detalle

    def _build_request(
        self,
        config: BillingProviderConfig,
        order_payload: dict,
        dte_type: int,
        receptor: dict,
        is_boleta: bool,
    ) -> dict:
        today_str = date.today().isoformat()
        total, mnt_neto, iva = self._split_iva(int(order_payload.get("total") or 0))
        detalle = self._build_detalle(order_payload.get("items") or [])
        if not detalle:
            raise AppError("El pedido no tiene líneas para facturar", 400)

        id_doc: dict = {
            "TipoDTE": dte_type,
            "FchEmis": today_str,
            "FchVenc": today_str,
        }
        if is_boleta:
            id_doc["IndServicioBoleta"] = 3

        emisor = {
            "RUTEmisor": config.emitter_rut,
            "RznSocEmisor": config.emitter_name,
            "GiroEmisor": config.emitter_activity,
            "DirOrigen": config.emitter_address,
            "CmnaOrigen": config.emitter_commune,
            "CiudadOrigen": config.emitter_city,
            "CorreoEmisor": config.emitter_email,
        }
        if not is_boleta:
            emisor["RznSoc"] = config.emitter_name
            emisor["GiroEmis"] = config.emitter_activity
            emisor["Telefono"] = []
            emisor["Acteco"] = [620200]

        receptor_body = {
            "RUTRecep": receptor.get("rut") or CONSUMIDOR_FINAL_RUT,
            "RznSocRecep": receptor.get("name") or order_payload.get("customer_name") or "Cliente",
            "DirRecep": receptor.get("address") or order_payload.get("shipping_address") or "",
            "CmnaRecep": receptor.get("commune") or order_payload.get("city") or "",
            "CiudadRecep": receptor.get("city") or order_payload.get("city") or "",
            "CorreoRecep": receptor.get("email") or order_payload.get("customer_email") or "",
        }
        if not is_boleta:
            receptor_body["GiroRecep"] = receptor.get("activity") or "Particular"

        totales = {
            "MntNeto": str(mnt_neto),
            "IVA": str(iva),
            "MntTotal": str(total),
        }
        if not is_boleta:
            totales["TasaIVA"] = "19"

        return {
            "Documento": {
                "Encabezado": {
                    "IdDoc": id_doc,
                    "Emisor": emisor,
                    "Receptor": receptor_body,
                    "Totales": totales,
                },
                "Detalle": detalle,
            },
            "Observaciones": f"Pedido {order_payload.get('order_number') or ''}".strip(),
            "TipoPago": "CONTADO",
            "Cajero": "Binfrix",
        }

    def _issue(
        self,
        config: BillingProviderConfig,
        body: dict,
        use_boleta_endpoint: bool,
    ) -> BillingIssueResult:
        token = self._token(config)
        branch = config.branch_name.strip() or "Casa Matriz"
        url = f"{config.base_url}/invoiceV2/{branch}"
        try:
            response = httpx.post(url, json=body, headers=self._headers(token), timeout=60.0)
        except httpx.HTTPError as exc:
            raise AppError(f"Error al emitir en SimpleFactura: {exc}", 502) from exc

        if response.status_code != 200:
            detail = response.text[:500]
            raise AppError(f"SimpleFactura rechazó la emisión: {detail}", 400)

        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise AppError("Respuesta inválida de SimpleFactura", 502)

        folio = data.get("folio")
        if folio is None:
            raise AppError("SimpleFactura no devolvió folio del documento", 502)

        return BillingIssueResult(
            dte_type=int(data.get("tipoDTE") or body["Documento"]["Encabezado"]["IdDoc"]["TipoDTE"]),
            folio=int(folio),
            emisor_rut=str(data.get("rutEmisor") or config.emitter_rut),
            receptor_rut=str(data.get("rutReceptor") or ""),
            total=float(data.get("total") or 0),
            fecha_emision=str(data.get("fechaEmision") or date.today().isoformat()),
        )

    def issue_boleta(
        self,
        config: BillingProviderConfig,
        order_payload: dict,
    ) -> BillingIssueResult:
        receptor = {
            "rut": CONSUMIDOR_FINAL_RUT,
            "name": order_payload.get("customer_name"),
            "email": order_payload.get("customer_email"),
            "address": order_payload.get("shipping_address"),
            "city": order_payload.get("city"),
        }
        body = self._build_request(config, order_payload, DTE_BOLETA, receptor, is_boleta=True)
        return self._issue(config, body, use_boleta_endpoint=True)

    def issue_factura(
        self,
        config: BillingProviderConfig,
        order_payload: dict,
        receptor: dict,
    ) -> BillingIssueResult:
        rut = (receptor.get("rut") or "").strip()
        if not rut:
            raise AppError("La factura requiere RUT del receptor", 400)
        if not (receptor.get("name") or "").strip():
            raise AppError("La factura requiere razón social del receptor", 400)
        if not (receptor.get("activity") or "").strip():
            raise AppError("La factura requiere giro del receptor", 400)

        body = self._build_request(config, order_payload, DTE_FACTURA, receptor, is_boleta=False)
        return self._issue(config, body, use_boleta_endpoint=False)

    def fetch_pdf(
        self,
        config: BillingProviderConfig,
        emisor_rut: str,
        dte_type: int,
        folio: int,
    ) -> bytes:
        token = self._token(config)
        url = f"{config.base_url}/dte/pdf"
        payload = {
            "credenciales": {
                "rutEmisor": emisor_rut,
                "nombreSucursal": config.branch_name,
            },
            "dteReferenciadoExterno": {
                "folio": folio,
                "codigoTipoDte": dte_type,
                "ambiente": 0,
            },
        }
        try:
            response = httpx.post(url, json=payload, headers=self._headers(token), timeout=60.0)
        except httpx.HTTPError as exc:
            raise AppError(f"Error al obtener PDF: {exc}", 502) from exc

        if response.status_code != 200:
            raise AppError(f"No se pudo obtener el PDF ({response.status_code})", 400)
        return response.content

    def resolve_config(
        self,
        enabled: bool,
        email: str,
        password: str,
        branch_name: str,
        emitter_rut: str,
        emitter_name: str,
        emitter_activity: str,
        emitter_address: str,
        emitter_commune: str,
        emitter_city: str,
        emitter_email: str,
    ) -> BillingProviderConfig | None:
        if not enabled:
            return None
        mail = (email or "").strip()
        secret = (password or "").strip()
        rut = (emitter_rut or "").strip()
        if not mail or not secret or not rut:
            return None
        return BillingProviderConfig(
            provider_id=self.provider_id,
            base_url=BASE_URL,
            email=mail,
            password=secret,
            branch_name=(branch_name or "Casa Matriz").strip(),
            emitter_rut=rut,
            emitter_name=(emitter_name or "Tienda").strip(),
            emitter_activity=(emitter_activity or "Venta de productos").strip(),
            emitter_address=(emitter_address or "Sin dirección").strip(),
            emitter_commune=(emitter_commune or "Santiago").strip(),
            emitter_city=(emitter_city or "Santiago").strip(),
            emitter_email=(emitter_email or mail).strip(),
        )
