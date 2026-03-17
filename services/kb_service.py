import json
from sqlalchemy.orm import Session
from models.kb_article import KBArticle
from schemas.kb_article import (
    KBArticleCreate,
    KBArticleUpdate,
    KBSearchResult,
    KBArticleOut,
)
from vector.chroma_client import delete_article, index_article, search_articles


def create_article(db: Session, payload: KBArticleCreate, author_id: str) -> KBArticle:
    article = KBArticle(
        title=payload.title,
        content=payload.content,
        tags=json.dumps(payload.tags),
        source_ticket_id=payload.source_ticket_id,
        author_id=author_id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_article(db: Session, article_id: str) -> KBArticle | None:
    return db.get(KBArticle, article_id)


def list_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
) -> tuple[list[KBArticle], int]:
    query = db.query(KBArticle)
    if status:
        query = query.filter(KBArticle.status == status)
    total = query.count()
    items = query.order_by(KBArticle.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_article(
    db: Session, article_id: str, payload: KBArticleUpdate
) -> KBArticle | None:
    article = db.get(KBArticle, article_id)
    if not article:
        return None

    data = payload.model_dump(exclude_none=True)
    if "tags" in data:
        data["tags"] = json.dumps(data["tags"])

    for field, value in data.items():
        setattr(article, field, value)

    if payload.status == "published":
        tags = json.loads(article.tags or "[]")
        index_article(article.id, article.title, article.content, tags)
        article.chroma_id = article.id
    elif payload.status == "archived" and article.chroma_id:
        delete_article(article.id)
        article.chroma_id = None

    db.commit()
    db.refresh(article)
    return article


def search_kb(db: Session, query: str, n_results: int = 3) -> list[KBSearchResult]:
    hits = search_articles(query, n_results=n_results)
    results = []
    for hit in hits:
        article = db.get(KBArticle, hit["id"])
        if article:
            results.append(
                KBSearchResult(
                    article=KBArticleOut.model_validate(article),
                    score=hit["score"],
                )
            )
    return results
