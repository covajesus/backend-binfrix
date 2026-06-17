from datetime import date

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.base import BaseRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.base import BaseService


class CustomerRepository(BaseRepository[Customer]):
    model = Customer


class CustomerService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = CustomerRepository(db, tenant_id=tenant_id)

    def list_customers(self) -> list[Customer]:
        return self.repo.list_all(order_by=Customer.created_at.desc())

    def get_customer(self, customer_id: str) -> Customer:
        return self.repo.get_by_id(customer_id)

    def create_customer(self, payload: CustomerCreate) -> Customer:
        customer = Customer(
            tenant_id=self.repo.tenant_id,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            email=str(payload.email),
            phone=payload.phone,
            city=payload.city,
            status=payload.status,
            notes=payload.notes,
            created_at=date.today(),
        )
        self.repo.add(customer)
        self.commit()
        return self.repo.refresh(customer)

    def update_customer(self, customer_id: str, payload: CustomerUpdate) -> Customer:
        customer = self.repo.get_by_id(customer_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, field, str(value) if field == "email" and value else value)
        self.commit()
        return self.repo.refresh(customer)

    def delete_customer(self, customer_id: str) -> None:
        customer = self.repo.get_by_id(customer_id)
        self.repo.delete(customer)
        self.commit()
