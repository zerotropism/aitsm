from datetime import datetime
from pydantic import BaseModel


class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    source: str = "portal"


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    category: str | None = None
    assignee_id: str | None = None


class TicketOut(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    category: str | None
    source: str
    requester_id: str
    assignee_id: str | None
    ai_triage_done: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketList(BaseModel):
    items: list[TicketOut]
    total: int
