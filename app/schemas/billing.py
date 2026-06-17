from typing import Literal

from pydantic import BaseModel, Field


class BillingReceptorIn(BaseModel):
    rut: str = ""
    name: str = ""
    activity: str = ""
    email: str = ""
    address: str = ""
    commune: str = ""
    city: str = ""


class BillingIssueIn(BaseModel):
    document_type: Literal["boleta", "factura"]
    receptor: BillingReceptorIn | None = None


class BillingDocumentOut(BaseModel):
    document_type: str = ""
    dte_type: int | None = None
    folio: int | None = None
    status: str = ""
    emisor_rut: str = ""
    receptor_rut: str = ""
    total: float | None = None
    fecha_emision: str = ""
    error: str = ""
    issued_at: str | None = None
