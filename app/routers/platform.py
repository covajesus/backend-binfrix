from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_platform_admin
from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.models.user import User
from app.schemas.blog_post import BlogPostCreate, BlogPostOut, BlogPostUpdate
from app.schemas.contact_message import ContactMessageOut, ContactMessageUpdate
from app.schemas.license import PlatformProductOut
from app.schemas.platform_admin import (
    PlatformClientCreate,
    PlatformClientOut,
    PlatformLicenseCreate,
    PlatformLicenseOut,
    PlatformLicenseUpdate,
    PlatformPlanOut,
)
from app.schemas.support_ticket import (
    SupportTicketMessageCreate,
    SupportTicketOut,
    SupportTicketUpdate,
)
from app.services.admin_service import PlatformAdminService
from app.services.blog_post_service import BlogPostService
from app.services.contact_message_service import ContactMessageService
from app.services.support_ticket_service import PlatformSupportTicketService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/clients", response_model=list[PlatformClientOut])
def list_platform_clients(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformClientOut]:
    return PlatformAdminService(db).list_clients()


@router.post("/clients", response_model=PlatformClientOut, status_code=status.HTTP_201_CREATED)
def create_platform_client(
    payload: PlatformClientCreate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> PlatformClientOut:
    try:
        return PlatformAdminService(db).create_client(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/plans", response_model=list[PlatformPlanOut])
def list_platform_plans(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformPlanOut]:
    rows = PlatformAdminService(db).list_plans()
    return [PlatformPlanOut(**row) for row in rows]


@router.get("/licenses", response_model=list[PlatformLicenseOut])
def list_platform_licenses(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformLicenseOut]:
    return PlatformAdminService(db).list_all_licenses()


@router.post("/licenses", response_model=PlatformLicenseOut, status_code=status.HTTP_201_CREATED)
def create_platform_license(
    payload: PlatformLicenseCreate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> PlatformLicenseOut:
    try:
        return PlatformAdminService(db).create_license(payload)
    except AppError as exc:
        raise_http(exc)


@router.patch("/licenses/{license_id}", response_model=PlatformLicenseOut)
def update_platform_license(
    license_id: str,
    payload: PlatformLicenseUpdate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> PlatformLicenseOut:
    try:
        return PlatformAdminService(db).update_license(license_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/licenses/{license_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_license(
    license_id: str,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> None:
    try:
        PlatformAdminService(db).delete_license(license_id)
    except AppError as exc:
        raise_http(exc)


@router.get("/products", response_model=list[PlatformProductOut])
def list_platform_products(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[PlatformProductOut]:
    rows = PlatformAdminService(db).list_platform_products()
    return [
        PlatformProductOut(
            id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
        )
        for row in rows
    ]


@router.get("/contact-messages", response_model=list[ContactMessageOut])
def list_platform_contact_messages(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[ContactMessageOut]:
    return ContactMessageService(db).list_all()


@router.get("/contact-messages/{message_id}", response_model=ContactMessageOut)
def get_platform_contact_message(
    message_id: str,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> ContactMessageOut:
    try:
        return ContactMessageService(db).get_by_id(message_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/contact-messages/{message_id}", response_model=ContactMessageOut)
def update_platform_contact_message(
    message_id: str,
    payload: ContactMessageUpdate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> ContactMessageOut:
    try:
        return ContactMessageService(db).update(message_id, payload)
    except AppError as exc:
        raise_http(exc)


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


@router.get("/blog-posts", response_model=list[BlogPostOut])
def list_platform_blog_posts(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[BlogPostOut]:
    return BlogPostService(db).list_posts()


@router.post("/blog-posts", response_model=BlogPostOut, status_code=status.HTTP_201_CREATED)
def create_platform_blog_post(
    payload: BlogPostCreate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> BlogPostOut:
    try:
        return BlogPostService(db).create(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/blog-posts/{post_id}", response_model=BlogPostOut)
def get_platform_blog_post(
    post_id: str,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> BlogPostOut:
    try:
        return BlogPostService(db).get_by_id(post_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/blog-posts/{post_id}", response_model=BlogPostOut)
def update_platform_blog_post(
    post_id: str,
    payload: BlogPostUpdate,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> BlogPostOut:
    try:
        return BlogPostService(db).update(post_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/blog-posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_blog_post(
    post_id: str,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> None:
    try:
        BlogPostService(db).delete(post_id)
    except AppError as exc:
        raise_http(exc)
