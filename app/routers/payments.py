from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentUpdate
from app.utils.payments import generate_payment_number, map_payment_status_to_order, today

router = APIRouter(prefix="/payments", tags=["payments"])


def _sync_order_payment(db: Session, order_id: str | None, payment_status: str) -> None:
    if not order_id:
        return
    order = db.get(Order, order_id)
    if order is None:
        return
    order.payment_status = map_payment_status_to_order(payment_status)


@router.get("", response_model=list[PaymentOut])
def list_payments(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.tenant_id == ctx.tenant.id)
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Payment:
    count = db.query(Payment).filter(Payment.tenant_id == ctx.tenant.id).count()
    paid_at = payload.paid_at
    if payload.status == "completed" and paid_at is None:
        paid_at = today()

    payment = Payment(
        tenant_id=ctx.tenant.id,
        payment_number=generate_payment_number(count),
        order_id=payload.order_id,
        order_number=payload.order_number,
        customer_name=payload.customer_name,
        amount=payload.amount,
        method=payload.method,
        status=payload.status,
        transaction_ref=payload.transaction_ref,
        notes=payload.notes,
        paid_at=paid_at,
        created_at=today(),
    )
    db.add(payment)
    db.flush()
    _sync_order_payment(db, payment.order_id, payment.status)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Payment:
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.tenant_id == ctx.tenant.id)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return payment


@router.patch("/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: str,
    payload: PaymentUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Payment:
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.tenant_id == ctx.tenant.id)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(payment, field, value)

    if payment.status == "completed" and payment.paid_at is None:
        payment.paid_at = date.today()

    _sync_order_payment(db, payment.order_id, payment.status)
    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.tenant_id == ctx.tenant.id)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    db.delete(payment)
    db.commit()
