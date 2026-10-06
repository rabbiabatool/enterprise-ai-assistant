import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import Base, engine, get_db
from backend.prompts import ANALYZE_SYSTEM, ASK_SYSTEM, build_ask_prompt
from backend.services.llm import LLMError, generate_structured

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Enterprise AI Assistant", lifespan=lifespan)


class Question(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/documents", response_model=schemas.DocumentOut, status_code=201)
def create_document(payload: schemas.DocumentCreate, db: Session = Depends(get_db)):
    doc = models.Document(**payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@app.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(category: str | None = None, db: Session = Depends(get_db)):
    query = select(models.Document)
    if category:
        query = query.where(models.Document.category == category)
    return db.scalars(query.order_by(models.Document.id)).all()


@app.get("/documents/{doc_id}", response_model=schemas.DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.post("/ask", response_model=schemas.AskResult)
def ask(question: Question, db: Session = Depends(get_db)):
    docs = db.scalars(select(models.Document).order_by(models.Document.id)).all()
    if not docs:
        return schemas.AskResult(
            answer="No documents have been uploaded yet.", source_ids=[], found=False
        )
    try:
        return generate_structured(
            build_ask_prompt(question.text, docs),
            schemas.AskResult,
            system=ASK_SYSTEM,
        )
    except LLMError as exc:
        raise HTTPException(
            status_code=502, detail="The AI service failed. Please try again."
        ) from exc


@app.post("/documents/{doc_id}/analyze", response_model=schemas.DocumentAnalysis)
def analyze_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        return generate_structured(
            f"<document>\n{doc.content}\n</document>",
            schemas.DocumentAnalysis,
            system=ANALYZE_SYSTEM,
        )
    except LLMError as exc:
        raise HTTPException(
            status_code=502, detail="The AI service failed. Please try again."
        ) from exc


@app.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()