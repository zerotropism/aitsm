"""The KB vector index. Chroma runs embedded; the embedding model is downloaded on first use."""

from __future__ import annotations

import chromadb
from chromadb.utils import embedding_functions

from aitsm.core.config import settings

_client: chromadb.PersistentClient | None = None


def get_collection() -> chromadb.Collection:
    """Open the collection, naming the embedding function rather than relying on the default.

    Chroma's default is all-MiniLM-L6-v2 in ONNX: no torch, but the model is downloaded on the
    first embedding into ~/.cache/chroma/onnx_models. Good enough for a KB of this size; swapping
    in a sentence-transformers model would improve recall at the cost of a heavy dependency.
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    return _client.get_or_create_collection(
        "kb_articles", embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )


def index_article(article_id: str, title: str, content: str, tags: list[str]) -> None:
    collection = get_collection()
    text = f"{title}\n{' '.join(tags)}\n{content}"
    collection.upsert(
        ids=[article_id],
        documents=[text],
        metadatas=[{"title": title, "tags": ",".join(tags)}],
    )


def delete_article(article_id: str) -> None:
    get_collection().delete(ids=[article_id])


def search_articles(query: str, n_results: int = 3) -> list[dict]:
    """Return matching article ids, best first.

    Chroma returns a distance, where lower is closer. It is converted to a similarity so that
    a higher `score` means a better match — which is what every caller, and every model
    reading the MCP output, assumes.
    """
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(n_results, count))
    return [
        {
            "id": article_id,
            "score": round(1.0 / (1.0 + results["distances"][0][index]), 4),
            "distance": round(results["distances"][0][index], 4),
        }
        for index, article_id in enumerate(results["ids"][0])
    ]
