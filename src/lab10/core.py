"""Pure tenant isolation policy and deterministic synthetic embeddings."""
from __future__ import annotations
import hashlib
import math
import re
from typing import Any

DIMENSIONS = 8
TENANT_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


def embedding(text: str) -> list[float]:
    """Non-ML, deterministic vectors; not a semantic embedding model."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [int.from_bytes(digest[i:i+4], "big") / 2**32 - 0.5 for i in range(0, 32, 4)]
    norm = math.sqrt(sum(value * value for value in raw)) or 1
    return [value / norm for value in raw]


def collection_name(strategy: str, tenant: str) -> str:
    if not TENANT_PATTERN.fullmatch(tenant):
        raise ValueError("Invalid synthetic tenant identifier")
    if strategy == "shared":
        return "esk_lab_10_shared"
    if strategy == "per_tenant":
        return f"esk_lab_10_{tenant}"
    raise ValueError("Unsupported strategy")


def tenant_filter(tenant: str) -> dict[str, Any]:
    return {"must": [{"key": "tenant_id", "match": {"value": tenant}}]}
