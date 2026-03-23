import json
from sqlalchemy.orm import Session
from models.kb_feedback import KBFeedback
from models.kb_article import KBArticle
from schemas.kb_article import (
    KBArticleCreate,
    KBArticleUpdate,
    KBSearchResult,
    KBArticleOut,
    FeedbackCreate,
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


def add_feedback(
    db: Session, article_id: str, payload: FeedbackCreate, user_id: str
) -> KBArticle:
    article = db.get(KBArticle, article_id)
    if not article:
        raise ValueError(f"Article {article_id} not found")
    if payload.vote not in ("useful", "not_relevant"):
        raise ValueError("vote must be 'useful' or 'not_relevant'")

    # To prevent multiple votes from same user on same article & ticket
    existing = (
        db.query(KBFeedback)
        .filter(
            KBFeedback.article_id == article_id,
            KBFeedback.user_id == user_id,
            KBFeedback.ticket_id == payload.ticket_id,
        )
        .first()
    )
    if existing:
        raise ValueError("Already voted for this article in this context")

    feedback = KBFeedback(
        article_id=article_id,
        ticket_id=payload.ticket_id,
        user_id=user_id,
        vote=payload.vote,
    )
    db.add(feedback)

    if payload.vote == "useful":
        article.useful_count += 1
    else:
        article.not_relevant_count += 1

    db.commit()
    db.refresh(article)
    return article
