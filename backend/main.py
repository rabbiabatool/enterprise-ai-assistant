from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Enterprise AI Assistant")


class Question(BaseModel):
    text: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask")
def ask(question: Question):
    return {"answer": f"You asked: {question.text}"}