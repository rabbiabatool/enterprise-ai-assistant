from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    category: str = "general"
    content: str


class DocumentOut(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class Category(str, Enum):
    hr = "hr"
    finance = "finance"
    legal = "legal"
    technical = "technical"
    sales = "sales"
    other = "other"


class DocumentAnalysis(BaseModel):
    summary: str
    category: Category
    key_points: list[str]


class AskResult(BaseModel):
    answer: str
    source_ids: list[int]
    found: bool