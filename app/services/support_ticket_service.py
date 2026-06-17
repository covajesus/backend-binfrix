import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.roles import is_platform_admin
from app.core.tenant_context import TenantContext
from app.models.support_ticket import SupportTicket
from app.models.tenant import Tenant
from app.repositories.base import BaseRepository
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketMessageCreate,
    SupportTicketMessageOut,
    SupportTicketOut,
    SupportTicketUpdate,
)
from app.services.base import BaseService
from app.utils.tickets import generate_ticket_number

VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}
VALID_PRIORITIES = {"low", "normal", "high"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SupportTicketRepository(BaseRepository[SupportTicket]):
    model = SupportTicket


def _platform_role_slug(ctx: TenantContext) -> str | None:
    role = ctx.user.role
    return role.slug if role is not None else None


def _can_manage_tickets(ctx: TenantContext) -> bool:
    if ctx.role == "admin":
        return True
    if ctx.user.is_superadmin:
        return True
    return is_platform_admin(_platform_role_slug(ctx))


def _author_role_label(ctx: TenantContext) -> str:
    if is_platform_admin(_platform_role_slug(ctx)) or ctx.user.is_superadmin:
        return "platform_admin"
    if ctx.role == "admin":
        return "tenant_admin"
    return "user"


def _serialize_messages(raw: list | None) -> list[SupportTicketMessageOut]:
    if not raw:
        return []
    result: list[SupportTicketMessageOut] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        body = str(item.get("body") or "").strip()
        if not body:
            continue
        created = item.get("created_at")
        if isinstance(created, str):
            try:
                created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                created_at = utcnow()
        elif isinstance(created, datetime):
            created_at = created
        else:
            created_at = utcnow()
        result.append(
            SupportTicketMessageOut(
                id=str(item.get("id") or uuid.uuid4()),
                author_user_id=str(item.get("author_user_id") or ""),
                author_name=str(item.get("author_name") or ""),
                author_role=str(item.get("author_role") or "user"),
                body=body,
                created_at=created_at,
            )
        )
    return result


def _serialize_ticket(ticket: SupportTicket, tenant_name: str | None = None) -> SupportTicketOut:
    return SupportTicketOut(
        id=ticket.id,
        tenant_id=ticket.tenant_id,
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        created_by_user_id=ticket.created_by_user_id,
        created_by_name=ticket.created_by_name,
        messages=_serialize_messages(ticket.messages),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        tenant_name=tenant_name,
    )


class SupportTicketService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = SupportTicketRepository(db, tenant_id=tenant_id)

    def _ticket_query_for_user(self, ctx: TenantContext):
        query = self.repo._base_query()
        if not _can_manage_tickets(ctx):
            query = query.filter(SupportTicket.created_by_user_id == ctx.user.id)
        return query

    def _get_ticket_by_id(self, ctx: TenantContext, ticket_id: str) -> SupportTicket:
        from app.core.exceptions import NotFoundError

        if is_platform_admin(_platform_role_slug(ctx)) or ctx.user.is_superadmin:
            ticket = (
                self.db.query(SupportTicket)
                .filter(SupportTicket.id == ticket_id)
                .first()
            )
        elif _can_manage_tickets(ctx):
            ticket = (
                self.repo._base_query()
                .filter(SupportTicket.id == ticket_id)
                .first()
            )
        else:
            ticket = (
                self.repo._base_query()
                .filter(
                    SupportTicket.id == ticket_id,
                    SupportTicket.created_by_user_id == ctx.user.id,
                )
                .first()
            )

        if ticket is None:
            raise NotFoundError("Ticket no encontrado")
        return ticket

    def list_tickets(self, ctx: TenantContext) -> list[SupportTicketOut]:
        rows = (
            self._ticket_query_for_user(ctx)
            .order_by(SupportTicket.updated_at.desc())
            .all()
        )
        return [_serialize_ticket(row) for row in rows]

    def get_ticket(self, ctx: TenantContext, ticket_id: str) -> SupportTicketOut:
        ticket = self._get_ticket_by_id(ctx, ticket_id)
        tenant_name = None
        if is_platform_admin(_platform_role_slug(ctx)) or ctx.user.is_superadmin:
            tenant = self.db.query(Tenant).filter(Tenant.id == ticket.tenant_id).first()
            tenant_name = tenant.name if tenant else None
        return _serialize_ticket(ticket, tenant_name=tenant_name)

    def create_ticket(self, ctx: TenantContext, payload: SupportTicketCreate) -> SupportTicketOut:
        priority = payload.priority.strip().lower()
        if priority not in VALID_PRIORITIES:
            priority = "normal"

        count = self.repo._base_query().count()
        author_name = ctx.user.name.strip() or ctx.user.email
        initial_message = {
            "id": str(uuid.uuid4()),
            "author_user_id": ctx.user.id,
            "author_name": author_name,
            "author_role": _author_role_label(ctx),
            "body": payload.description.strip(),
            "created_at": utcnow().isoformat(),
        }

        ticket = SupportTicket(
            tenant_id=self.repo.tenant_id,
            ticket_number=generate_ticket_number(count),
            subject=payload.subject.strip(),
            description=payload.description.strip(),
            status="open",
            priority=priority,
            created_by_user_id=ctx.user.id,
            created_by_name=author_name,
            messages=[initial_message],
        )
        self.repo.add(ticket)
        self.commit()
        return _serialize_ticket(self.repo.refresh(ticket))

    def update_ticket(
        self,
        ctx: TenantContext,
        ticket_id: str,
        payload: SupportTicketUpdate,
    ) -> SupportTicketOut:
        if not _can_manage_tickets(ctx):
            raise ForbiddenError("No tienes permiso para actualizar este ticket")

        ticket = self._get_ticket_by_id(ctx, ticket_id)
        data = payload.model_dump(exclude_unset=True)

        if "status" in data and data["status"] is not None:
            status = data["status"].strip().lower()
            if status in VALID_STATUSES:
                ticket.status = status

        if "priority" in data and data["priority"] is not None:
            priority = data["priority"].strip().lower()
            if priority in VALID_PRIORITIES:
                ticket.priority = priority

        self.commit()
        return _serialize_ticket(self.repo.refresh(ticket))

    def add_message(
        self,
        ctx: TenantContext,
        ticket_id: str,
        payload: SupportTicketMessageCreate,
    ) -> SupportTicketOut:
        ticket = self._get_ticket_by_id(ctx, ticket_id)
        if ticket.status == "closed":
            raise ForbiddenError("El ticket está cerrado")

        author_name = ctx.user.name.strip() or ctx.user.email
        message = {
            "id": str(uuid.uuid4()),
            "author_user_id": ctx.user.id,
            "author_name": author_name,
            "author_role": _author_role_label(ctx),
            "body": payload.body.strip(),
            "created_at": utcnow().isoformat(),
        }

        messages = list(ticket.messages or [])
        messages.append(message)
        ticket.messages = messages

        if _can_manage_tickets(ctx) and ticket.status == "open":
            ticket.status = "in_progress"

        self.commit()
        return _serialize_ticket(self.repo.refresh(ticket))


class PlatformSupportTicketService(BaseService):
    def _get_ticket_row(self, ticket_id: str) -> tuple[SupportTicket, str]:
        from app.core.exceptions import NotFoundError

        row = (
            self.db.query(SupportTicket, Tenant.name)
            .join(Tenant, Tenant.id == SupportTicket.tenant_id)
            .filter(SupportTicket.id == ticket_id)
            .first()
        )
        if row is None:
            raise NotFoundError("Ticket no encontrado")
        return row[0], row[1]

    def list_all_tickets(self) -> list[SupportTicketOut]:
        rows = (
            self.db.query(SupportTicket, Tenant.name)
            .join(Tenant, Tenant.id == SupportTicket.tenant_id)
            .order_by(SupportTicket.updated_at.desc())
            .all()
        )
        return [_serialize_ticket(ticket, tenant_name=tenant_name) for ticket, tenant_name in rows]

    def get_ticket(self, ticket_id: str) -> SupportTicketOut:
        ticket, tenant_name = self._get_ticket_row(ticket_id)
        return _serialize_ticket(ticket, tenant_name=tenant_name)

    def update_ticket(
        self,
        user,
        ticket_id: str,
        payload: SupportTicketUpdate,
    ) -> SupportTicketOut:
        ticket, _ = self._get_ticket_row(ticket_id)
        tenant = self.db.query(Tenant).filter(Tenant.id == ticket.tenant_id).first()
        ctx = TenantContext(user=user, tenant=tenant, role="admin")
        SupportTicketService(self.db, tenant_id=ticket.tenant_id).update_ticket(
            ctx, ticket_id, payload
        )
        return self.get_ticket(ticket_id)

    def add_message(
        self,
        user,
        ticket_id: str,
        payload: SupportTicketMessageCreate,
    ) -> SupportTicketOut:
        ticket, _ = self._get_ticket_row(ticket_id)
        tenant = self.db.query(Tenant).filter(Tenant.id == ticket.tenant_id).first()
        ctx = TenantContext(user=user, tenant=tenant, role="admin")
        SupportTicketService(self.db, tenant_id=ticket.tenant_id).add_message(
            ctx, ticket_id, payload
        )
        return self.get_ticket(ticket_id)
