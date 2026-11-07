"""ESK-LAB-10 G3-R2E: real-HTTP two-tenant isolation regression.

Synthetic fixtures only. Never addresses any service except the configured
loopback LAB10 API and loopback Qdrant health endpoint. Never alters Docker.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

PROJECT = Path(__file__).resolve().parents[1]
EVIDENCE = PROJECT / "evidence" / "G3_R2E_HTTP_RESULT.json"
BASE = "http://127.0.0.1:18010"
QDRANT_HEALTH = "http://127.0.0.1:6333/healthz"
TOKEN = {"tenant_a": "demo-tenant-a-token", "tenant_b": "demo-tenant-b-token"}
RUN_ID = uuid.uuid4().hex


def main() -> int:
    results: list[dict] = []
    fixtures: dict[str, dict] = {}
    failures: list[str] = []
    initial_error = None

    def check(name: str, passed: bool, detail: str = "") -> None:
        results.append({"check": name, "passed": bool(passed), "detail": detail})
        print(f"{name}={'PASS' if passed else 'FAIL'}" + (f" ({detail})" if detail else ""), flush=True)
        if not passed:
            failures.append(name)

    def req(client: httpx.Client, method: str, path: str, who: str | None = None, body=None) -> httpx.Response:
        headers = {"Authorization": f"Bearer {TOKEN[who]}"} if who in TOKEN else (
            {"Authorization": "Bearer invalid-token"} if who == "invalid" else {}
        )
        return client.request(method, path, headers=headers, json=body)

    def status(client, name, method, path, expected, who=None, body=None):
        r = req(client, method, path, who, body)
        check(name, r.status_code == expected, f"expected={expected} actual={r.status_code}")
        return r

    if EVIDENCE.exists():
        print(f"EVIDENCE_EXISTS_HOLD={EVIDENCE}", flush=True)
        return 2
    if urlparse(BASE).hostname not in ("127.0.0.1", "localhost"):
        print("NON_LOOPBACK_API_HOLD", flush=True)
        return 2
    if urlparse(QDRANT_HEALTH).hostname not in ("127.0.0.1", "localhost"):
        print("NON_LOOPBACK_QDRANT_HOLD", flush=True)
        return 2

    print("=== ESK-LAB-10 G3-R2E REAL HTTP TWO-TENANT GATE ===", flush=True)
    print("FIXTURES=SYNTHETIC", flush=True)
    print("STRATEGY=ACTIVE_SERVER_CONFIGURATION_NOT_INDEPENDENTLY_PROVEN", flush=True)
    print(f"RUN_ID={RUN_ID}", flush=True)
    try:
        with httpx.Client(base_url=BASE, timeout=15.0, trust_env=False) as client:
            try:
                identity = client.get("/openapi.json")
                if identity.status_code != 200 or identity.json().get("info", {}).get("title") != "ESK-LAB-10 Tenant Retrieval Demo":
                    raise RuntimeError("API_IDENTITY_HOLD")
                check("API_IDENTITY", True)
                health = client.get("/health")
                if health.status_code != 200 or health.json().get("status") != "api_up":
                    raise RuntimeError("API_HEALTH_HOLD")
                check("API_HEALTH", True)
                with httpx.Client(timeout=10.0, trust_env=False) as qclient:
                    qr = qclient.get(QDRANT_HEALTH)
                if qr.status_code != 200:
                    raise RuntimeError("QDRANT_HEALTH_HOLD")
                check("QDRANT_HEALTH", True)

                status(client, "NO_AUTH", "GET", "/documents", 401)
                status(client, "INVALID_AUTH", "GET", "/documents", 401, "invalid")
                status(client, "FORGED_TENANT_ID", "POST", "/documents", 422, "tenant_a", {"content": "synthetic", "tenant_id": "tenant_b"})

                for tenant in ("tenant_a", "tenant_b"):
                    content = f"ESKLAB10-G3R2E-{RUN_ID}-{tenant}-original"
                    created = status(client, f"{tenant.upper()}_CREATE", "POST", "/documents", 201, tenant, {"content": content})
                    if created.status_code != 201:
                        raise RuntimeError(f"FIXTURE_CREATE_FAILED_{tenant}")
                    data = created.json()
                    try:
                        uuid.UUID(str(data.get("id", "")))
                    except (ValueError, TypeError, AttributeError) as exc:
                        raise RuntimeError(f"FIXTURE_BAD_ID_{tenant}") from exc
                    if data.get("tenant_id") != tenant:
                        raise RuntimeError(f"FIXTURE_WRONG_OWNER_{tenant}")
                    fixtures[tenant] = {"id": data["id"], "original": content, "latest": content}

                for owner, intruder in (("tenant_a", "tenant_b"), ("tenant_b", "tenant_a")):
                    doc_id = fixtures[owner]["id"]
                    prefix = f"{intruder.upper()}_TO_{owner.upper()}"
                    status(client, f"{prefix}_READ_DENIED", "GET", f"/documents/{doc_id}", 404, intruder)
                    status(client, f"{prefix}_REINDEX_DENIED", "PUT", f"/documents/{doc_id}/reindex", 404, intruder, {"content": f"unauthorized-{RUN_ID}"})
                    status(client, f"{prefix}_DELETE_DENIED", "DELETE", f"/documents/{doc_id}", 404, intruder)

                for tenant in ("tenant_a", "tenant_b"):
                    doc_id = fixtures[tenant]["id"]
                    own = status(client, f"{tenant.upper()}_OWNER_READ", "GET", f"/documents/{doc_id}", 200, tenant)
                    if own.status_code == 200:
                        payload = own.json()
                        check(f"{tenant.upper()}_OWNER_CONTENT", payload.get("id") == doc_id and payload.get("tenant_id") == tenant and payload.get("content") == fixtures[tenant]["original"])
                    updated = f"ESKLAB10-G3R2E-{RUN_ID}-{tenant}-updated"
                    reindexed = status(client, f"{tenant.upper()}_REINDEX", "PUT", f"/documents/{doc_id}/reindex", 200, tenant, {"content": updated})
                    if reindexed.status_code == 200:
                        fixtures[tenant]["latest"] = updated
                    reread = status(client, f"{tenant.upper()}_UPDATED_READ", "GET", f"/documents/{doc_id}", 200, tenant)
                    if reread.status_code == 200:
                        data = reread.json()
                        check(f"{tenant.upper()}_UPDATED_CONTENT", data.get("content") == updated and data.get("tenant_id") == tenant)

                for tenant in ("tenant_a", "tenant_b"):
                    own_id = fixtures[tenant]["id"]
                    foreign_id = fixtures["tenant_b" if tenant == "tenant_a" else "tenant_a"]["id"]
                    for label, method, path, body in (
                        ("LIST", "GET", "/documents", None),
                        ("SEARCH", "POST", "/search", {"query": fixtures["tenant_b" if tenant == "tenant_a" else "tenant_a"]["latest"], "limit": 20}),
                    ):
                        response = status(client, f"{tenant.upper()}_{label}_HTTP", method, path, 200, tenant, body)
                        if response.status_code != 200:
                            continue
                        payload = response.json()
                        proper_shape = isinstance(payload, list) and all(isinstance(i, dict) for i in payload)
                        check(f"{tenant.upper()}_{label}_JSON_ARRAY", proper_shape)
                        if not proper_shape:
                            continue
                        check(f"{tenant.upper()}_{label}_ISOLATION", all(x.get("tenant_id") == tenant and x.get("id") != foreign_id for x in payload), f"item_count={len(payload)}")
                        if label == "LIST":
                            check(f"{tenant.upper()}_LIST_INCLUDES_OWN", any(x.get("id") == own_id for x in payload))
            except Exception as exc:
                initial_error = f"{type(exc).__name__}: {exc}"
                check("EXECUTION", False, initial_error)
            finally:
                for tenant, fixture in fixtures.items():
                    try:
                        # Do not delete a document until exact server-owned identity/content match.
                        looked = req(client, "GET", f"/documents/{fixture['id']}", tenant)
                        safe = looked.status_code == 200 and looked.json().get("id") == fixture["id"] and looked.json().get("tenant_id") == tenant and looked.json().get("content") in (fixture["original"], fixture["latest"])
                        check(f"{tenant.upper()}_CLEANUP_IDENTITY", safe)
                        if not safe:
                            continue
                        removed = req(client, "DELETE", f"/documents/{fixture['id']}", tenant)
                        check(f"{tenant.upper()}_CLEANUP_DELETE", removed.status_code == 200 and removed.json().get("deleted") is True, f"actual={removed.status_code}")
                        verify = req(client, "GET", f"/documents/{fixture['id']}", tenant)
                        check(f"{tenant.upper()}_CLEANUP_VERIFIED", verify.status_code == 404, f"actual={verify.status_code}")
                    except Exception as exc:
                        check(f"{tenant.upper()}_CLEANUP_ERROR", False, f"{type(exc).__name__}: {exc}")
    except Exception as exc:
        check("TOP_LEVEL_ERROR", False, f"{type(exc).__name__}: {exc}")
    finally:
        record = {
            "gate": "G3-R2E",
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "run_id": RUN_ID,
            "transport": "real_http",
            "api": BASE,
            "data": "synthetic_only",
            "strategy": "active_server_configuration_not_independently_proven",
            "fixtures": {key: value["id"] for key, value in fixtures.items()},
            "results": results,
            "failure_count": len(failures),
            "execution_error": initial_error,
            "status": "PASS" if not failures and len(fixtures) == 2 else "HOLD",
        }
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        with EVIDENCE.open("x", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
            f.write("\n")
        print(f"FAILURES={len(failures)}", flush=True)
        print(f"G3_R2E_STATUS={record['status']}", flush=True)
        print(f"EVIDENCE_FILE={EVIDENCE}", flush=True)
        print("DOCKER_MODIFICATIONS=NONE", flush=True)
    return 0 if not failures and len(fixtures) == 2 else 1


if __name__ == "__main__":
    sys.exit(main())
