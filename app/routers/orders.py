from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.billing import BillingDocumentOut, BillingIssueIn
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate
from app.services.billing_service import BillingService
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


def _service(ctx: TenantContext, db: Session) -> OrderService:
    return OrderService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[OrderOut])
def list_orders(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[OrderOut]:
    return _service(ctx, db).list_orders()


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> OrderOut:
    try:
        return _service(ctx, db).create_order(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> OrderOut:
    try:
        return _service(ctx, db).get_order(order_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: str,
    payload: OrderUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> OrderOut:
    try:
        return _service(ctx, db).update_order(order_id, payload)
    except AppError as exc:
        raise_http(exc)


def _billing_service(ctx: TenantContext, db: Session) -> BillingService:
    return BillingService(db, tenant_id=ctx.tenant.id)


@router.get("/{order_id}/billing", response_model=BillingDocumentOut)
def get_order_billing(
    order_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> BillingDocumentOut:
    try:
        return _billing_service(ctx, db).get_billing_status(order_id)
    except AppError as exc:
        raise_http(exc)


@router.post("/{order_id}/billing/issue", response_model=BillingDocumentOut)
def issue_order_billing(
    order_id: str,
    payload: BillingIssueIn,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> BillingDocumentOut:
    try:
        return _billing_service(ctx, db).issue_document(order_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{order_id}/billing/pdf")
def download_order_billing_pdf(
    order_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Response:
    try:
        pdf_bytes, filename = _billing_service(ctx, db).fetch_pdf(order_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except AppError as exc:
        raise_http(exc)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_order(order_id)
    except AppError as exc:
        raise_http(exc)
