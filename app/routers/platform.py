from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_platform_admin
from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.models.user import User
from app.schemas.platform_admin import PlatformClientOut, PlatformLicenseOut
from app.schemas.support_ticket import (
    SupportTicketMessageCreate,
    SupportTicketOut,
    SupportTicketUpdate,
)
from app.services.admin_service import PlatformAdminService
from app.services.support_ticket_service import PlatformSupportTicketService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/clients", response_model=list[PlatformClientOut])
def list_platform_clients(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformClientOut]:
    return PlatformAdminService(db).list_clients()


@router.get("/licenses", response_model=list[PlatformLicenseOut])
def list_platform_licenses(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformLicenseOut]:
    return PlatformAdminService(db).list_all_licenses()


@router.get("/support-tickets", response_model=list[SupportTicketOut])
def list_platform_support_tickets(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[SupportTicketOut]:
    return PlatformSupportTicketService(db).list_all_tickets()


@router.get("/support-tickets/{ticket_id}", response_model=SupportTicketOut)
def get_platform_support_ticket(
    ticket_id: str,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return PlatformSupportTicketService(db).get_ticket(ticket_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/support-tickets/{ticket_id}", response_model=SupportTicketOut)
def update_platform_support_ticket(
    ticket_id: str,
    payload: SupportTicketUpdate,
    user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return PlatformSupportTicketService(db).update_ticket(user, ticket_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.post(
    "/support-tickets/{ticket_id}/messages",
    response_model=SupportTicketOut,
    status_code=status.HTTP_200_OK,
)
def add_platform_support_ticket_message(
    ticket_id: str,
    payload: SupportTicketMessageCreate,
    user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> SupportTicketOut:
    try:
        return PlatformSupportTicketService(db).add_message(user, ticket_id, payload)
    except AppError as exc:
        raise_http(exc)
