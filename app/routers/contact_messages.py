from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, raise_http
from app.db.session import get_db
from app.schemas.contact_message import ContactMessageCreate, ContactMessageOut
from app.services.contact_message_service import ContactMessageService

router = APIRouter(prefix="/contact-messages", tags=["contact-messages"])


@router.post("", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
def create_contact_message(
    payload: ContactMessageCreate,
    db: Session = Depends(get_db),
) -> ContactMessageOut:
    try:
        return ContactMessageService(db).create(payload)
    except AppError as exc:
        raise_http(exc)
