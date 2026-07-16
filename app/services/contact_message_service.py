from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.models.contact_message import ContactMessage
from app.repositories.base import BaseRepository
from app.schemas.contact_message import ContactMessageCreate, ContactMessageOut, ContactMessageUpdate
from app.services.base import BaseService

VALID_STATUSES = {"new", "read"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContactMessageRepository(BaseRepository[ContactMessage]):
    model = ContactMessage


class ContactMessageService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = ContactMessageRepository(db, tenant_id=None)

    def _to_out(self, row: ContactMessage) -> ContactMessageOut:
        return ContactMessageOut(
            id=row.id,
            name=row.name,
            phone=row.phone,
            email=row.email,
            interest=row.interest,
            status=row.status,
            created_at=row.created_at,
            read_at=row.read_at,
        )

    def create(self, payload: ContactMessageCreate) -> ContactMessageOut:
        row = ContactMessage(
            name=payload.name.strip(),
            phone=payload.phone.strip(),
            email=str(payload.email).strip().lower(),
            interest=payload.interest.strip(),
            status="new",
        )
        self.repo.add(row)
        self.commit()
        return self._to_out(self.repo.refresh(row))

    def list_all(self) -> list[ContactMessageOut]:
        rows = (
            self.db.query(ContactMessage)
            .order_by(ContactMessage.created_at.desc())
            .all()
        )
        return [self._to_out(row) for row in rows]

    def get_by_id(self, message_id: str) -> ContactMessageOut:
        row = self.db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        if row is None:
            raise NotFoundError("Mensaje no encontrado")
        return self._to_out(row)

    def update(self, message_id: str, payload: ContactMessageUpdate) -> ContactMessageOut:
        row = self.db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        if row is None:
            raise NotFoundError("Mensaje no encontrado")

        if payload.status is not None:
            status = payload.status.strip().lower()
            if status not in VALID_STATUSES:
                raise AppError("Estado no válido")
            row.status = status
            if status == "read" and row.read_at is None:
                row.read_at = utcnow()
            if status == "new":
                row.read_at = None

        self.commit()
        self.db.refresh(row)
        return self._to_out(row)
