from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.kb_article import KBArticleOut, KBSearchResult
from schemas.ticket import TicketOut
from services.ai_service import (
    deflect,
    draft_kb_article,
    suggest_kb_articles,
    suggest_reply,
    triage_ticket,
)

router = APIRouter()


@router.get("/deflect", response_model=list[KBSearchResult])
def deflect_ticket(
    q: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deflect(db, query=q)


@router.post("/tickets/{ticket_id}/triage", response_model=TicketOut)
def triage(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return triage_ticket(db, ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/tickets/{ticket_id}/suggest-kb", response_model=list[KBSearchResult])
def suggest_kb(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return suggest_kb_articles(db, ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tickets/{ticket_id}/draft-article", response_model=KBArticleOut)
def draft_article(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return draft_kb_article(db, ticket_id, author_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/tickets/{ticket_id}/suggest-reply", response_model=dict)
def suggest_reply_endpoint(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        reply = suggest_reply(db, ticket_id)
        return {"reply": reply}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
