from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate
from app.utils.orders import calc_order_total, generate_order_number, normalize_line_items, today

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
def list_orders(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[Order]:
    return (
        db.query(Order)
        .filter(Order.tenant_id == ctx.tenant.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Order:
    count = db.query(Order).filter(Order.tenant_id == ctx.tenant.id).count()
    items = normalize_line_items([item.model_dump() for item in payload.items])
    order = Order(
        tenant_id=ctx.tenant.id,
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
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Order:
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.tenant_id == ctx.tenant.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: str,
    payload: OrderUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> Order:
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.tenant_id == ctx.tenant.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "items" in data and data["items"] is not None:
        items = normalize_line_items(data["items"])
        order.items = items
        order.total = calc_order_total(items)
        data.pop("items")

    for field, value in data.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.tenant_id == ctx.tenant.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    db.delete(order)
    db.commit()
