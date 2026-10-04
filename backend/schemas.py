from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    category: str = "general"
    content: str


class DocumentOut(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime