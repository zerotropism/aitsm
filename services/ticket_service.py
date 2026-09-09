from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from core.config import settings
from models.ticket import Ticket
from models.ticket_comment import TicketComment
from schemas.ticket import TicketCreate, TicketUpdate
from schemas.ticket_comment import CommentCreate


def _compute_sla_due(priority: str, from_dt: datetime) -> datetime:
    hours = settings.SLA_HOURS.get(priority, 24)
    return from_dt + timedelta(hours=hours)


def create_ticket(db: Session, payload: TicketCreate, requester_id: str) -> Ticket:
    now = datetime.now(UTC)
    ticket = Ticket(
        **payload.model_dump(),
        requester_id=requester_id,
        sla_due_at=_compute_sla_due(payload.priority, now),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _check_sla(db: Session, ticket: Ticket) -> Ticket:
    if (
        not ticket.sla_breached
        and ticket.sla_due_at
        and ticket.status not in ("resolved", "closed")
    ):
        now = datetime.now(UTC)
        due = ticket.sla_due_at
        # Normalize : if due is naive, interpret it as UTC
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        if now > due:
            ticket.sla_breached = True
            db.commit()
            db.refresh(ticket)
    return ticket


def get_ticket(db: Session, ticket_id: str) -> Ticket | None:
    ticket = db.get(Ticket, ticket_id)
    if ticket:
        ticket = _check_sla(db, ticket)
    return ticket


def list_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    priority: str | None = None,
    sla_breached: bool | None = None,
) -> tuple[list[Ticket], int]:
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if sla_breached is not None:
        query = query.filter(Ticket.sla_breached == sla_breached)
    total = query.count()
    items = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_ticket(db: Session, ticket_id: str, payload: TicketUpdate) -> Ticket | None:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        return None

    data = payload.model_dump(exclude_none=True)

    # Si la priorité change, recalculer le SLA
    if "priority" in data and data["priority"] != ticket.priority:
        ticket.sla_due_at = _compute_sla_due(data["priority"], datetime.now(UTC))
        # Réinitialiser le breach si on remonte la priorité
        ticket.sla_breached = False

    for field, value in data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket


def add_comment(
    db: Session, ticket_id: str, payload: CommentCreate, author_id: str
) -> TicketComment:
    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=author_id,
        content=payload.content,
        is_internal=payload.is_internal,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, ticket_id: str) -> list[TicketComment]:
    return (
        db.query(TicketComment)
        .filter(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at.asc())
        .all()
    )
