import json

from pydantic import BaseModel, field_validator


class ServiceCatalogCreate(BaseModel):
    name: str
    description: str
    category: str
    default_priority: str = "medium"
    form_schema: list[dict] = []


class ServiceCatalogOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    default_priority: str
    form_schema: list[dict]
    is_active: bool

    model_config = {"from_attributes": True}

    @field_validator("form_schema", mode="before")
    @classmethod
    def parse_form_schema(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        if v is None:
            return []
        return v


class ServiceRequestCreate(BaseModel):
    form_data: dict = {}
