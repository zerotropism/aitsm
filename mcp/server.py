import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

import services.ai_service as ai_svc
import services.kb_service as kb_svc
import services.ticket_service as ticket_svc
from core.config import settings
from core.database import SessionLocal
from schemas.ticket import TicketCreate, TicketUpdate
from schemas.ticket_comment import CommentCreate

mcp = FastMCP("aitsm")

SYSTEM_USER_ID = settings.MCP_SYSTEM_USER_ID


def get_db():
    return SessionLocal()


# Tickets
@mcp.tool()
def create_ticket(
    title: str, description: str, priority: str = "medium", source: str = "portal"
) -> dict:
    """Create a new ITSM ticket."""
    db = get_db()
    try:
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
    finally:
        db.close()


@mcp.tool()
def list_tickets(
    status: str | None, priority: str | None, sla_breached: bool | None, limit: int = 20
) -> list[dict]:
    """List tickets with optional filters on status, priority, and SLA."""
    db = get_db()
    try:
        items, total = ticket_svc.list_tickets(
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
    finally:
        db.close()


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Get the full details of a ticket by its ID."""
    db = get_db()
    try:
        t = ticket_svc.get_ticket(db, ticket_id)
        if not t:
            return {"error": f"Ticket {ticket_id} not found"}
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
    finally:
        db.close()


@mcp.tool()
def update_ticket(
    ticket_id: str,
    status: str | None,
    priority: str | None,
    category: str | None,
    resolution: str | None,
    assignee_id: str | None,
) -> dict:
    """Update a ticket (status, priority, category, resolution, assignee)."""
    db = get_db()
    try:
        payload = TicketUpdate(
            status=status,
            priority=priority,
            category=category,
            resolution=resolution,
            assignee_id=assignee_id,
        )
        t = ticket_svc.update_ticket(db, ticket_id, payload)
        if not t:
            return {"error": f"Ticket {ticket_id} not found"}
        return {
            "id": t.id,
            "status": t.status,
            "priority": t.priority,
            "category": t.category,
        }
    finally:
        db.close()


@mcp.tool()
def add_comment(ticket_id: str, content: str, is_internal: bool = False) -> dict:
    """Add a comment to a ticket."""
    db = get_db()
    try:
        payload = CommentCreate(content=content, is_internal=is_internal)
        c = ticket_svc.add_comment(db, ticket_id, payload, author_id=SYSTEM_USER_ID)
        return {
            "id": c.id,
            "ticket_id": c.ticket_id,
            "content": c.content,
            "is_internal": c.is_internal,
        }
    finally:
        db.close()


# Knowledge Base
@mcp.tool()
def search_kb(query: str, n_results: int = 3) -> list[dict]:
    """Semantic search in the published knowledge base."""
    db = get_db()
    try:
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
    finally:
        db.close()


# AI
@mcp.tool()
def triage_ticket(ticket_id: str) -> dict:
    """Run AI triage on a ticket: automatically fills in category and priority."""
    db = get_db()
    try:
        t = ai_svc.triage_ticket(db, ticket_id)
        return {
            "id": t.id,
            "category": t.category,
            "priority": t.priority,
            "ai_triage_done": t.ai_triage_done,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()


@mcp.tool()
def suggest_kb_for_ticket(ticket_id: str) -> list[dict]:
    """Suggest the most relevant KB articles for an existing ticket."""
    db = get_db()
    try:
        results = ai_svc.suggest_kb_articles(db, ticket_id)
        return [{"id": r.article.id, "title": r.article.title, "score": r.score} for r in results]
    except ValueError as e:
        return [{"error": str(e)}]
    finally:
        db.close()


@mcp.tool()
def deflect(query: str) -> list[dict]:
    """Suggest KB articles from a free-form question before creating a ticket."""
    db = get_db()
    try:
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
    finally:
        db.close()


@mcp.tool()
def suggest_reply(ticket_id: str) -> dict:
    """Generate a suggested reply for a ticket to be validated by the agent."""
    db = get_db()
    try:
        reply = ai_svc.suggest_reply(db, ticket_id)
        return {"ticket_id": ticket_id, "reply": reply}
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()


@mcp.tool()
def draft_kb_article(ticket_id: str) -> dict:
    """Generate a draft KB article from a resolved ticket (draft status, to be validated)."""
    db = get_db()
    try:
        article = ai_svc.draft_kb_article(db, ticket_id, author_id=SYSTEM_USER_ID)
        return {
            "id": article.id,
            "title": article.title,
            "status": article.status,
            "source_ticket_id": article.source_ticket_id,
        }
    except ValueError as e:
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
