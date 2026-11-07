"""Qdrant REST transport. All document operations enforce server tenant filters."""
from __future__ import annotations
import os
from typing import Any
from urllib.parse import quote
import httpx
from .core import DIMENSIONS, collection_name, tenant_filter, embedding

class QdrantStore:
    def __init__(self):
        self.base = os.getenv("LAB10_QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
        self.strategy = os.getenv("LAB10_STRATEGY", "shared")
        if self.strategy not in ("shared", "per_tenant"):
            raise RuntimeError("Invalid LAB10_STRATEGY")

    def _request(self, method: str, path: str, body: dict | None = None) -> Any:
        with httpx.Client(timeout=10.0, trust_env=False) as client:
            resp = client.request(method, self.base + path, json=body)
            resp.raise_for_status()
            return resp.json()

    def _path(self, tenant: str) -> str:
        return "/collections/" + quote(collection_name(self.strategy, tenant), safe="")

    def ensure(self, tenant: str) -> None:
        path = self._path(tenant)
        with httpx.Client(timeout=10.0, trust_env=False) as client:
            response = client.get(self.base + path)
            if response.status_code == 404:
                created = client.put(self.base + path, json={"vectors": {"size": DIMENSIONS, "distance": "Cosine"}})
                created.raise_for_status()
            else:
                response.raise_for_status()

    def _collection_exists(self, tenant: str) -> bool:
        """Check only the server-derived tenant collection."""
        path = self._path(tenant)
        with httpx.Client(timeout=10.0, trust_env=False) as client:
            response = client.get(self.base + path)
            if response.status_code == 404:
                return False
            response.raise_for_status()
            return True

    def get(self, tenant: str, document_id: str) -> dict | None:
        """Use a filtered scroll, never an unfiltered ID lookup."""
        if not self._collection_exists(tenant):
            return None
        data = self._request("POST", self._path(tenant) + "/points/scroll", {
            "filter": {"must": tenant_filter(tenant)["must"] + [{"has_id": [document_id]}]},
            "limit": 1, "with_payload": True, "with_vector": False,
        })
        points = data.get("result", {}).get("points", [])
        return points[0] if points else None

    def put(self, tenant: str, document_id: str, content: str) -> None:
        self.ensure(tenant)
        self._request("PUT", self._path(tenant) + "/points?wait=true", {
            "points": [{"id": document_id, "vector": embedding(content),
                        "payload": {"tenant_id": tenant, "content": content}}]})

    def search(self, tenant: str, text: str, limit: int = 5) -> list[dict]:
        self.ensure(tenant)
        data = self._request("POST", self._path(tenant) + "/points/query", {
            "query": embedding(text), "filter": tenant_filter(tenant),
            "limit": limit, "with_payload": True, "with_vector": False,
        })
        return data.get("result", {}).get("points", [])

    def list_documents(self, tenant: str) -> list[dict]:
        self.ensure(tenant)
        data = self._request("POST", self._path(tenant) + "/points/scroll", {
            "filter": tenant_filter(tenant), "limit": 100,
            "with_payload": True, "with_vector": False,
        })
        return data.get("result", {}).get("points", [])

    def delete(self, tenant: str, document_id: str) -> bool:
        if self.get(tenant, document_id) is None:
            return False
        # Filtered delete acts as an additional server-side tenant boundary.
        self._request("POST", self._path(tenant) + "/points/delete?wait=true", {
            "filter": {"must": tenant_filter(tenant)["must"] + [{"has_id": [document_id]}]}})
        return True
