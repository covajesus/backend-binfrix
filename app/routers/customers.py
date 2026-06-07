from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerOut])
def list_customers(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.tenant_id == ctx.tenant.id)
        .order_by(Customer.created_at.desc())
        .all()
    )


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Customer:
    customer = Customer(
        tenant_id=ctx.tenant.id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=str(payload.email),
        phone=payload.phone,
        city=payload.city,
        status=payload.status,
        notes=payload.notes,
        created_at=date.today(),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Customer:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.tenant_id == ctx.tenant.id)
        .first()
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Customer:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.tenant_id == ctx.tenant.id)
        .first()
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, str(value) if field == "email" and value else value)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.tenant_id == ctx.tenant.id)
        .first()
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(customer)
    db.commit()
