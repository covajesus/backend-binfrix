from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


def _service(ctx: TenantContext, db: Session) -> CustomerService:
    return CustomerService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[CustomerOut])
def list_customers(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[CustomerOut]:
    return _service(ctx, db).list_customers()


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CustomerOut:
    try:
        return _service(ctx, db).create_customer(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CustomerOut:
    try:
        return _service(ctx, db).get_customer(customer_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CustomerOut:
    try:
        return _service(ctx, db).update_customer(customer_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_customer(customer_id)
    except AppError as exc:
        raise_http(exc)
