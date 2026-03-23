from sqlalchemy.orm import Session
from models.ticket import Ticket
from models.ticket_comment import TicketComment
from schemas.ticket import TicketCreate, TicketUpdate
from schemas.ticket_comment import CommentCreate


def create_ticket(db: Session, payload: TicketCreate, requester_id: str) -> Ticket:
    ticket = Ticket(**payload.model_dump(), requester_id=requester_id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket(db: Session, ticket_id: str) -> Ticket | None:
    return db.get(Ticket, ticket_id)


def list_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    priority: str | None = None,
) -> tuple[list[Ticket], int]:
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    total = query.count()
    items = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_ticket(db: Session, ticket_id: str, payload: TicketUpdate) -> Ticket | None:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        return None
    for field, value in payload.model_dump(exclude_none=True).items():
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
