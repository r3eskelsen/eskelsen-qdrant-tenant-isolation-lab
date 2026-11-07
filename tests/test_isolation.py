"""In-memory contract tests. Does NOT count as live Qdrant verification."""
import uuid
from fastapi.testclient import TestClient
from lab10.api import app, store
from lab10.core import tenant_filter, collection_name, embedding

class FakeStore:
    def __init__(self):
        self.data = {}
    def put(self, tenant, doc_id, content):
        self.data[(tenant, doc_id)] = {"id": doc_id, "payload": {"tenant_id": tenant, "content": content}}
    def get(self, tenant, doc_id):
        return self.data.get((tenant, doc_id))
    def list_documents(self, tenant):
        return [point for (t, _), point in self.data.items() if t == tenant]
    def search(self, tenant, text, limit):
        return self.list_documents(tenant)[:limit]
    def delete(self, tenant, doc_id):
        return self.data.pop((tenant, doc_id), None) is not None


def test_adversarial_isolation():
    fake = FakeStore()
    app.dependency_overrides[store] = lambda: fake
    try:
        client = TestClient(app)
        a = {"Authorization": "Bearer demo-tenant-a-token"}
        b = {"Authorization": "Bearer demo-tenant-b-token"}
        created = client.post("/documents", headers=a, json={"content": "Alpha secret fixture"})
        assert created.status_code == 201
        doc_id = created.json()["id"]
        assert client.get(f"/documents/{doc_id}", headers=a).status_code == 200
        assert client.get(f"/documents/{doc_id}", headers=b).status_code == 404
        assert client.get("/documents", headers=b).json() == []
        assert client.post("/search", headers=b, json={"query": "Alpha"}).json() == []
        assert client.put(f"/documents/{doc_id}/reindex", headers=b, json={"content": "Hacked"}).status_code == 404
        assert client.delete(f"/documents/{doc_id}", headers=b).status_code == 404
        assert client.get(f"/documents/{doc_id}", headers=a).json()["content"] == "Alpha secret fixture"
        assert client.post("/documents", headers=a, json={"content": "x", "tenant_id": "tenant_b"}).status_code == 422
        assert client.get("/documents", headers={}).status_code == 401
        assert client.get("/documents", headers={"Authorization": "Bearer invalid"}).status_code == 401
        assert client.put(f"/documents/{doc_id}/reindex", headers=a, json={"content": "Updated"}).status_code == 200
        assert client.delete(f"/documents/{doc_id}", headers=a).status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_filter_and_strategy():
    assert tenant_filter("tenant_a")["must"][0]["match"]["value"] == "tenant_a"
    assert collection_name("shared", "tenant_a") == collection_name("shared", "tenant_b")
    assert collection_name("per_tenant", "tenant_a") != collection_name("per_tenant", "tenant_b")
    assert len(embedding("test")) == 8
