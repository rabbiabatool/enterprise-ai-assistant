from fastapi.testclient import TestClient
from backend.main import app

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_rejects_bad_input(client):
    response = client.post("/ask", json={})
    assert response.status_code == 422


# def test_health():
#     response = client.get("/health")
#     assert response.status_code == 200
#     assert response.json() == {"status": "ok"}


# def test_ask_echoes_question():
#     response = client.post("/ask", json={"text": "hello"})
#     assert response.status_code == 200
#     assert "hello" in response.json()["answer"]


# def test_ask_rejects_bad_input():
#     response = client.post("/ask", json={})
#     assert response.status_code == 422