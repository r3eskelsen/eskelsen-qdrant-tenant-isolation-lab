"""Synthetic-only lab: public demo tokens are never production credentials."""
from __future__ import annotations
import hmac
import uuid
from functools import lru_cache
from fastapi import FastAPI, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from .store import QdrantStore

TOKENS = {"demo-tenant-a-token": "tenant_a", "demo-tenant-b-token": "tenant_b"}
app = FastAPI(title="ESK-LAB-10 Tenant Retrieval Demo", docs_url="/docs")

class DocumentIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    model_config = {"extra": "forbid"}

class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    model_config = {"extra": "forbid"}


def tenant(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    provided = authorization[7:]
    for token, tenant_id in TOKENS.items():
        if hmac.compare_digest(provided, token):
            return tenant_id
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid demo token")

@lru_cache
def store() -> QdrantStore:
    return QdrantStore()


def public(point: dict) -> dict:
    payload = point.get("payload", {})
    return {"id": str(point["id"]), "content": payload.get("content", ""),
            "tenant_id": payload.get("tenant_id"), **({"score": point["score"]} if "score" in point else {})}

@app.get("/health")
def health():
    return {"status": "api_up", "qdrant_checked": False}

@app.post("/documents", status_code=201)
def create_document(body: DocumentIn, tenant_id: str = Depends(tenant), backend: QdrantStore = Depends(store)):
    document_id = str(uuid.uuid4())
    backend.put(tenant_id, document_id, body.content)
    return {"id": document_id, "tenant_id": tenant_id}

@app.get("/documents")
def documents(tenant_id: str = Depends(tenant), backend: QdrantStore = Depends(store)):
    return [public(p) for p in backend.list_documents(tenant_id)]

@app.get("/documents/{document_id}")
def get_document(document_id: uuid.UUID, tenant_id: str = Depends(tenant), backend: QdrantStore = Depends(store)):
    point = backend.get(tenant_id, str(document_id))
    if point is None:
        raise HTTPException(404, "Document not found")
    return public(point)

@app.post("/search")
def search(body: SearchIn, tenant_id: str = Depends(tenant), backend: QdrantStore = Depends(store)):
    return [public(p) for p in backend.search(tenant_id, body.query, body.limit)]

@app.put("/documents/{document_id}/reindex")
def reindex(document_id: uuid.UUID, body: DocumentIn, tenant_id: str = Depends(tenant), backend: QdrantStore = Depends(store)):
    if backend.get(tenant_id, str(document_id)) is None:
        raise HTTPException(404, "Document not found")
    backend.put(tenant_id, str(document_id), body.content)
    return {"id": str(document_id), "tenant_id": tenant_id, "reindexed": True}

@app.delete("/documents/{document_id}")
def delete_document(document_id: uuid.UUID, tenant_id: str = Depends(tenant), backend: QdrantStore = Depends(store)):
    if not backend.delete(tenant_id, str(document_id)):
        raise HTTPException(404, "Document not found")
    return {"deleted": True}
