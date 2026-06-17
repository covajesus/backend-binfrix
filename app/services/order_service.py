from sqlalchemy.orm import Session

from app.models.order import Order
from app.repositories.base import BaseRepository
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.base import BaseService
from app.utils.orders import calc_order_total, generate_order_number, normalize_line_items, today


class OrderRepository(BaseRepository[Order]):
    model = Order

    def find_by_order_number(self, order_number: str) -> Order | None:
        return self._base_query().filter(Order.order_number == order_number).first()


class OrderService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = OrderRepository(db, tenant_id=tenant_id)

    def list_orders(self) -> list[Order]:
        return self.repo.list_all(order_by=Order.created_at.desc())

    def get_order(self, order_id: str) -> Order:
        return self.repo.get_by_id(order_id)

    def create_order(self, payload: OrderCreate) -> Order:
        count = self.repo._base_query().count()
        items = normalize_line_items([item.model_dump() for item in payload.items])
        order = Order(
            tenant_id=self.repo.tenant_id,
            order_number=generate_order_number(count),
            customer_id=payload.customer_id,
            customer_name=payload.customer_name.strip(),
            customer_email=payload.customer_email,
            customer_phone=payload.customer_phone,
            shipping_address=payload.shipping_address,
            city=payload.city,
            status=payload.status,
            payment_status=payload.payment_status,
            items=items,
            total=calc_order_total(items),
            notes=payload.notes,
            created_at=today(),
        )
        self.repo.add(order)
        self.commit()
        return self.repo.refresh(order)

    def update_order(self, order_id: str, payload: OrderUpdate) -> Order:
        order = self.repo.get_by_id(order_id)
        data = payload.model_dump(exclude_unset=True)
        if "items" in data and data["items"] is not None:
            items = normalize_line_items(data["items"])
            order.items = items
            order.total = calc_order_total(items)
            data.pop("items")

        for field, value in data.items():
            setattr(order, field, value)

        self.commit()
        return self.repo.refresh(order)

    def delete_order(self, order_id: str) -> None:
        order = self.repo.get_by_id(order_id)
        self.repo.delete(order)
        self.commit()
