from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketMessageCreate,
    SupportTicketOut,
    SupportTicketUpdate,
)
from app.services.support_ticket_service import SupportTicketService

router = APIRouter(prefix="/support-tickets", tags=["support-tickets"])


def _service(ctx: TenantContext, db: Session) -> SupportTicketService:
    return SupportTicketService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[SupportTicketOut])
def list_support_tickets(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[SupportTicketOut]:
    return _service(ctx, db).list_tickets(ctx)


@router.post("", response_model=SupportTicketOut, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: SupportTicketCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return _service(ctx, db).create_ticket(ctx, payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{ticket_id}", response_model=SupportTicketOut)
def get_support_ticket(
    ticket_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return _service(ctx, db).get_ticket(ctx, ticket_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{ticket_id}", response_model=SupportTicketOut)
def update_support_ticket(
    ticket_id: str,
    payload: SupportTicketUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return _service(ctx, db).update_ticket(ctx, ticket_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.post("/{ticket_id}/messages", response_model=SupportTicketOut)
def add_support_ticket_message(
    ticket_id: str,
    payload: SupportTicketMessageCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return _service(ctx, db).add_message(ctx, ticket_id, payload)
    except AppError as exc:
        raise_http(exc)
