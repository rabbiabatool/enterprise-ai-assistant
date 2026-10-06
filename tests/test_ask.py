from backend import schemas
from backend.services.llm import LLMError


def add_doc(client):
    return client.post(
        "/documents",
        json={"title": "Refund Policy", "category": "finance", "content": "30 days."},
    )


def test_ask_returns_structured_answer(client, monkeypatch):
    add_doc(client)
    fake = schemas.AskResult(answer="30 days.", source_ids=[1], found=True)
    monkeypatch.setattr("backend.main.generate_structured", lambda *a, **k: fake)

    response = client.post("/ask", json={"text": "Refund window?"})

    assert response.status_code == 200
    assert response.json()["source_ids"] == [1]
    assert response.json()["found"] is True


def test_ask_with_no_documents_skips_llm(client, monkeypatch):
    def should_not_be_called(*a, **k):
        raise AssertionError("LLM should not be called")

    monkeypatch.setattr("backend.main.generate_structured", should_not_be_called)

    response = client.post("/ask", json={"text": "Anything?"})

    assert response.status_code == 200
    assert response.json()["found"] is False


def test_ask_returns_502_when_llm_fails(client, monkeypatch):
    add_doc(client)

    def boom(*a, **k):
        raise LLMError("down")

    monkeypatch.setattr("backend.main.generate_structured", boom)

    response = client.post("/ask", json={"text": "Refund window?"})

    assert response.status_code == 502


def test_ask_rejects_empty_question(client):
    assert client.post("/ask", json={"text": ""}).status_code == 422