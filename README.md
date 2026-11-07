# Eskelsen Qdrant Multi-Tenant Retrieval Lab

**Independent, synthetic FastAPI + Qdrant isolation demonstration.**

**Public package:** v1.0.1 (documentation and test-runner portability corrections; underlying API/store isolation implementation unchanged).

**Evidence status (2026-11-06):** 2/2 in-memory pytest tests independently rerun successfully during package audit. Source-supplied records report successful live Qdrant tests in shared and per-tenant strategies and 44/44 real-HTTP adversarial checks on an active, **unverified strategy**. Those live runs were not independently reproduced during this publication audit. See [Verification Summary](docs/VERIFICATION_SUMMARY.md) for exact scope.

**Not production-ready, security-certified, a semantic search benchmark, or a public hosted service.**

## What the demo demonstrates

- A Python/FastAPI API for tenant-scoped document create, read, list, search, reindex, and delete operations.
- Synthetic bearer tokens mapped to trusted server-side tenant identities.
- Shared Qdrant collection with tenant payload filtering, or per-tenant collection selection.
- A synthetic, deterministic SHA-256-based vectorizer (8 dimensions); **not semantic machine-learning embeddings**.
- Negative tests involving forged tenant selectors, cross-tenant point IDs, unauthorized modification/deletion, and scoped search.
- An isolated Docker Compose service for Qdrant, bound to `127.0.0.1:6333`.

## Requirements

- Python 3.11 or newer; access to install Python packages.
- Docker Desktop/Compose only if running the local Qdrant integration checks.
- An isolated test machine; do not point this demo at existing services or client datasets.
- Local TCP ports `6333` (Qdrant) and `18010` (FastAPI) available.

## Setup on Windows PowerShell

From the extracted repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q tests/test_isolation.py
```

For optional live integration, after inspecting your Docker context, resources, and port ownership:

```powershell
docker compose -f compose.lab10.yml up -d qdrant
$env:LAB10_QDRANT_URL = 'http://127.0.0.1:6333'
$env:LAB10_STRATEGY = 'shared'
.\.venv\Scripts\python.exe scripts/G3-LIVE-SMOKE.py
```

The live smoke runner exercises both `shared` and `per_tenant` strategies against Qdrant using FastAPI TestClient. It writes synthetic fixtures and attempts cleanup. Run only against a dedicated disposable lab instance.

For the separate **real HTTP** test, start the application in a separate PowerShell terminal after configuring `LAB10_STRATEGY`:

```powershell
$env:LAB10_QDRANT_URL = 'http://127.0.0.1:6333'
$env:LAB10_STRATEGY = 'shared'
.\.venv\Scripts\python.exe -m uvicorn lab10.api:app --host 127.0.0.1 --port 18010
```

In a second terminal from the same repository root:

```powershell
.\.venv\Scripts\python.exe scripts/ESK-LAB-10-G3-R2E-HTTP-ADVERSARIAL.py
```

The real-HTTP runner is **loopback-only** and writes `evidence/G3_R2E_HTTP_RESULT.json` (which is ignored by Git). If this file already exists, the runner stops instead of overwriting it; preserve old evidence and use a fresh test workspace for a new run. Its active collection strategy is not independently asserted by the test script.

API docs when running: <http://127.0.0.1:18010/docs>

To stop the dedicated Qdrant container without intentionally deleting persistent storage:

```powershell
docker compose -f compose.lab10.yml stop qdrant
```

Stop manually launched Uvicorn separately using Ctrl+C. Do not use `down -v` for routine cleanup.

## Safety and limitations

- Demo tokens `demo-tenant-a-token` and `demo-tenant-b-token` are intentionally public and provide **no real authentication security**.
- Qdrant is **unauthenticated** on the local loopback port and can be reached by other local processes. Do not expose Qdrant or the API to untrusted networks.
- Tenant filtering must never be treated as a complete security boundary against a privileged Qdrant client, compromised host, incorrect configuration, or concurrent ownership races.
- Listing is limited to the first 100 points (no full pagination), and this lab does not prove production concurrency, high availability, RBAC, rate limits, credential rotation, scale, or vector retrieval relevance.
- No actual client data, enterprise credentials, or commercial API/provider calls are involved.
- Live integration records are historical evidence supplied with the release materials; **no independent fresh Docker/Qdrant run was performed in this packaging audit**.
- `LAB10_QDRANT_URL` and `LAB10_STRATEGY` are read from process environment; `.env.example` is informational and is not loaded automatically.

## Repository documentation

- `docs/ARCHITECTURE.md` — architecture and collection-strategy decisions.
- `docs/THREAT_MODEL.md` — documented threats and residual risks.
- `docs/TEST_PLAN.md` — mapped checks and unverified portions.
- `docs/VERIFICATION_SUMMARY.md` — recorded evidence, independent rerun, and limitations.
- `docs/RELEASE_GATES.md` — honest G0–G6 status.
- `docs/PORTFOLIO_FACTS.md` — verifiable descriptions suitable for Upwork.

## License

MIT License, Copyright (c) 2026 Eskelsen Systems. See [LICENSE](LICENSE).
