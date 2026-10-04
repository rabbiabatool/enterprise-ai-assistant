def make_doc(client, **overrides):
    data = {"title": "Refund Policy", "category": "finance", "content": "30 days."}
    data.update(overrides)
    return client.post("/documents", json=data)


def test_create_document(client):
    response = make_doc(client)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Refund Policy"


def test_list_and_filter(client):
    make_doc(client)
    make_doc(client, title="Leave Policy", category="hr")
    assert len(client.get("/documents").json()) == 2
    finance = client.get("/documents", params={"category": "finance"}).json()
    assert len(finance) == 1


def test_get_missing_document_returns_404(client):
    assert client.get("/documents/999").status_code == 404


def test_create_requires_content(client):
    response = client.post("/documents", json={"title": "No content"})
    assert response.status_code == 422