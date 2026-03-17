from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.kb_article import (
    KBArticleCreate,
    KBArticleOut,
    KBArticleUpdate,
    KBSearchResult,
)
from services.kb_service import (
    create_article,
    get_article,
    list_articles,
    search_kb,
    update_article,
)
from vector.chroma_client import delete_article

router = APIRouter()


@router.post("", response_model=KBArticleOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: KBArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_article(db, payload, author_id=current_user.id)


@router.get("/search", response_model=list[KBSearchResult])
def search(
    q: str = Query(..., min_length=3),
    n: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_kb(db, query=q, n_results=n)


@router.get("", response_model=list[KBArticleOut])
def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, _ = list_articles(db, skip=skip, limit=limit, status=status)
    return items


@router.get("/{article_id}", response_model=KBArticleOut)
def get_one(
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = get_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=KBArticleOut)
def update(
    article_id: str,
    payload: KBArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = update_article(db, article_id, payload)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    article = get_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.chroma_id:
        delete_article(article.id)
    db.delete(article)
    db.commit()
