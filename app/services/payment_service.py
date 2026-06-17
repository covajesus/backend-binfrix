from datetime import date

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import Payment
from app.repositories.base import BaseRepository
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.base import BaseService
from app.utils.payments import generate_payment_number, map_payment_status_to_order, today


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    def find_latest_for_order(self, order_id: str) -> Payment | None:
        return (
            self._base_query()
            .filter(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
            .first()
        )

    def count_all(self) -> int:
        return self._base_query().count()


class PaymentService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = PaymentRepository(db, tenant_id=tenant_id)

    def _sync_order_payment(self, order_id: str | None, payment_status: str) -> None:
        if not order_id:
            return
        order = self.db.get(Order, order_id)
        if order is None:
            return
        order.payment_status = map_payment_status_to_order(payment_status)

    def list_payments(self) -> list[Payment]:
        return self.repo.list_all(order_by=Payment.created_at.desc())

    def get_payment(self, payment_id: str) -> Payment:
        return self.repo.get_by_id(payment_id)

    def create_payment(self, payload: PaymentCreate) -> Payment:
        count = self.repo._base_query().count()
        paid_at = payload.paid_at
        if payload.status == "completed" and paid_at is None:
            paid_at = today()

        payment = Payment(
            tenant_id=self.repo.tenant_id,
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
        self.repo.add(payment)
        self._sync_order_payment(payment.order_id, payment.status)
        self.commit()
        return self.repo.refresh(payment)

    def update_payment(self, payment_id: str, payload: PaymentUpdate) -> Payment:
        payment = self.repo.get_by_id(payment_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(payment, field, value)

        if payment.status == "completed" and payment.paid_at is None:
            payment.paid_at = date.today()

        self._sync_order_payment(payment.order_id, payment.status)
        self.commit()
        return self.repo.refresh(payment)

    def delete_payment(self, payment_id: str) -> None:
        payment = self.repo.get_by_id(payment_id)
        self.repo.delete(payment)
        self.commit()
