"""Optional live integration gate. Requires explicitly started local Qdrant."""
from __future__ import annotations
import os
from fastapi.testclient import TestClient
from lab10.api import app, store
from lab10.store import QdrantStore


def execute(strategy):
    os.environ['LAB10_STRATEGY'] = strategy
    store.cache_clear()
    client = TestClient(app, raise_server_exceptions=True)
    a = {'Authorization': 'Bearer demo-tenant-a-token'}
    b = {'Authorization': 'Bearer demo-tenant-b-token'}
    created = client.post('/documents', headers=a, json={'content': 'Synthetic isolated payload A'})
    assert created.status_code == 201, created.text
    doc_id = created.json()['id']
    try:
        assert client.get(f'/documents/{doc_id}', headers=b).status_code == 404
        assert all(item['tenant_id'] == 'tenant_b' for item in client.get('/documents', headers=b).json())
        assert all(item['tenant_id'] == 'tenant_b' for item in client.post('/search', headers=b, json={'query': 'Synthetic isolated payload A'}).json())
        assert client.put(f'/documents/{doc_id}/reindex', headers=b, json={'content': 'forbidden'}).status_code == 404
        assert client.delete(f'/documents/{doc_id}', headers=b).status_code == 404
        assert client.get(f'/documents/{doc_id}', headers=a).status_code == 200
        assert client.put(f'/documents/{doc_id}/reindex', headers=a, json={'content': 'Synthetic updated A'}).status_code == 200
        assert client.get(f'/documents/{doc_id}', headers=a).json()['content'] == 'Synthetic updated A'
        print(f'LIVE_{strategy.upper()}_ISOLATION=PASS')
    finally:
        response = client.delete(f'/documents/{doc_id}', headers=a)
        print(f'LIVE_{strategy.upper()}_FIXTURE_CLEANUP_STATUS={response.status_code}')

if __name__ == '__main__':
    for strategy in ('shared', 'per_tenant'):
        execute(strategy)
