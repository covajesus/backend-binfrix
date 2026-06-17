from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentUpdate
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


def _service(ctx: TenantContext, db: Session) -> PaymentService:
    return PaymentService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[PaymentOut])
def list_payments(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[PaymentOut]:
    return _service(ctx, db).list_payments()


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> PaymentOut:
    try:
        return _service(ctx, db).create_payment(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> PaymentOut:
    try:
        return _service(ctx, db).get_payment(payment_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: str,
    payload: PaymentUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> PaymentOut:
    try:
        return _service(ctx, db).update_payment(payment_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_payment(payment_id)
    except AppError as exc:
        raise_http(exc)
