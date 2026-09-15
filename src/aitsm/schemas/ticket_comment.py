from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    content: str
    is_internal: bool = False


class CommentOut(BaseModel):
    id: str
    ticket_id: str
    author_id: str
    content: str
    is_internal: bool
    created_at: datetime

    model_config = {"from_attributes": True}
