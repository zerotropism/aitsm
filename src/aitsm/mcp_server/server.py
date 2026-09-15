from collections.abc import Iterator
from contextlib import contextmanager

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from sqlalchemy.orm import Session

import aitsm.services.ai_service as ai_svc
import aitsm.services.kb_service as kb_svc
import aitsm.services.ticket_service as ticket_svc
from aitsm.core.config import settings
from aitsm.core.database import SessionLocal
from aitsm.schemas.ticket import TicketCreate, TicketUpdate
from aitsm.schemas.ticket_comment import CommentCreate

mcp = FastMCP("aitsm")

SYSTEM_USER_ID = settings.MCP_SYSTEM_USER_ID


@contextmanager
def session() -> Iterator[Session]:
    """One session per tool call, always closed.

    Business failures raised inside are re-raised as ToolError: the client gets a clean
    message instead of a server-side traceback, and the model sees a failed call rather
    than a successful one carrying an {"error": ...} payload it has to notice.
    """
    db = SessionLocal()
    try:
        yield db
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        db.close()


# Tickets
@mcp.tool
def create_ticket(
    title: str, description: str, priority: str = "medium", source: str = "portal"
) -> dict:
    """Create a new ITSM ticket."""
    with session() as db:
        payload = TicketCreate(
            title=title, description=description, priority=priority, source=source
        )
        t = ticket_svc.create_ticket(db, payload, requester_id=SYSTEM_USER_ID)
        return {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "sla_due_at": str(t.sla_due_at),
        }


@mcp.tool
def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    sla_breached: bool | None = None,
    limit: int = 20,
) -> list[dict]:
    """List tickets with optional filters on status, priority, and SLA."""
    with session() as db:
        items, _total = ticket_svc.list_tickets(
            db, limit=limit, status=status, priority=priority, sla_breached=sla_breached
        )
        return [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "sla_breached": t.sla_breached,
            }
            for t in items
        ]


@mcp.tool
def get_ticket(ticket_id: str) -> dict:
    """Get the full details of a ticket by its ID."""
    with session() as db:
        t = ticket_svc.get_ticket(db, ticket_id)
        if not t:
            raise ToolError(f"Ticket {ticket_id} not found")
        return {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "category": t.category,
            "resolution": t.resolution,
            "sla_breached": t.sla_breached,
            "ai_triage_done": t.ai_triage_done,
        }


@mcp.tool
def update_ticket(
    ticket_id: str,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    resolution: str | None = None,
    assignee_id: str | None = None,
) -> dict:
    """Update a ticket (status, priority, category, resolution, assignee)."""
    with session() as db:
        payload = TicketUpdate(
            status=status,
            priority=priority,
            category=category,
            resolution=resolution,
            assignee_id=assignee_id,
        )
        t = ticket_svc.update_ticket(db, ticket_id, payload)
        if not t:
            raise ToolError(f"Ticket {ticket_id} not found")
        return {
            "id": t.id,
            "status": t.status,
            "priority": t.priority,
            "category": t.category,
        }


@mcp.tool
def add_comment(ticket_id: str, content: str, is_internal: bool = False) -> dict:
    """Add a comment to a ticket."""
    with session() as db:
        payload = CommentCreate(content=content, is_internal=is_internal)
        c = ticket_svc.add_comment(db, ticket_id, payload, author_id=SYSTEM_USER_ID)
        return {
            "id": c.id,
            "ticket_id": c.ticket_id,
            "content": c.content,
            "is_internal": c.is_internal,
        }


# Knowledge Base
@mcp.tool
def search_kb(query: str, n_results: int = 3) -> list[dict]:
    """Semantic search in the published knowledge base."""
    with session() as db:
        results = kb_svc.search_kb(db, query, n_results=n_results)
        return [
            {
                "id": r.article.id,
                "title": r.article.title,
                "score": r.score,
                "content": r.article.content[:500],
            }
            for r in results
        ]


# AI
@mcp.tool
def triage_ticket(ticket_id: str) -> dict:
    """Run AI triage on a ticket: automatically fills in category and priority."""
    with session() as db:
        t = ai_svc.triage_ticket(db, ticket_id)
        return {
            "id": t.id,
            "category": t.category,
            "priority": t.priority,
            "ai_triage_done": t.ai_triage_done,
        }


@mcp.tool
def suggest_kb_for_ticket(ticket_id: str) -> list[dict]:
    """Suggest the most relevant KB articles for an existing ticket."""
    with session() as db:
        results = ai_svc.suggest_kb_articles(db, ticket_id)
        return [{"id": r.article.id, "title": r.article.title, "score": r.score} for r in results]


@mcp.tool
def deflect(query: str) -> list[dict]:
    """Suggest KB articles from a free-form question before creating a ticket."""
    with session() as db:
        results = ai_svc.deflect(db, query)
        return [
            {
                "id": r.article.id,
                "title": r.article.title,
                "score": r.score,
                "content": r.article.content[:300],
            }
            for r in results
        ]


@mcp.tool
def suggest_reply(ticket_id: str) -> dict:
    """Generate a suggested reply for a ticket to be validated by the agent."""
    with session() as db:
        reply = ai_svc.suggest_reply(db, ticket_id)
        return {"ticket_id": ticket_id, "reply": reply}


@mcp.tool
def draft_kb_article(ticket_id: str) -> dict:
    """Generate a draft KB article from a resolved ticket (draft status, to be validated)."""
    with session() as db:
        article = ai_svc.draft_kb_article(db, ticket_id, author_id=SYSTEM_USER_ID)
        return {
            "id": article.id,
            "title": article.title,
            "status": article.status,
            "source_ticket_id": article.source_ticket_id,
        }


def main() -> None:
    """Console entry point: serve the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
