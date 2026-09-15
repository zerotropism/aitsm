from datetime import datetime

from pydantic import BaseModel


class ChangeCreate(BaseModel):
    title: str
    description: str
    risk: str = "medium"
    planned_at: datetime | None = None


class ChangeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    risk: str | None = None
    planned_at: datetime | None = None


class ChangeOut(BaseModel):
    id: str
    title: str
    description: str
    status: str
    risk: str
    planned_at: datetime | None
    submitter_id: str
    approver_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
