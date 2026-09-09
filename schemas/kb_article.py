import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class KBArticleCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []
    source_ticket_id: str | None = None


class KBArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class KBArticleOut(BaseModel):
    id: str
    title: str
    content: str
    tags: list[str]
    status: str
    author_id: str
    source_ticket_id: str | None
    chroma_id: str | None
    created_at: datetime
    updated_at: datetime
    useful_count: int
    not_relevant_count: int

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        if v is None:
            return []
        return v


class KBSearchResult(BaseModel):
    article: KBArticleOut
    score: float


class FeedbackCreate(BaseModel):
    vote: str  # "useful" | "not_relevant"
    ticket_id: str | None = None
