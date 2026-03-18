from __future__ import annotations
import chromadb
from core.config import settings


_client: chromadb.PersistentClient | None = None


def get_collection() -> chromadb.Collection:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    return _client.get_or_create_collection("kb_articles")


def index_article(article_id: str, title: str, content: str, tags: list[str]) -> None:
    collection = get_collection()
    text = f"{title}\n{' '.join(tags)}\n{content}"
    collection.upsert(
        ids=[article_id],
        documents=[text],
        metadatas=[{"title": title, "tags": ",".join(tags)}],
    )


def delete_article(article_id: str) -> None:
    collection = get_collection()
    collection.delete(ids=[article_id])


def search_articles(query: str, n_results: int = 3) -> list[dict]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, count),
    )
    items = []
    for i, article_id in enumerate(results["ids"][0]):
        items.append(
            {
                "id": article_id,
                "score": results["distances"][0][i],
            }
        )
    return items
