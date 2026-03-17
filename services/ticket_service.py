from sqlalchemy.orm import Session
from models.ticket import Ticket
from schemas.ticket import TicketCreate, TicketUpdate


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
