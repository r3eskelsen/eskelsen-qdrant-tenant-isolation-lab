# LAB-10 — Test Coverage Matrix

This file maps the original X01–X12 goals to the public source and recorded evidence. A PASS in a limited test is **not** whole-system security certification.

| ID | Scope | Supported result | Unverified remainder |
|---|---|---|---|
| X01 | Forged tenant input | Rejected body `tenant_id` (422), in-memory and supplied HTTP report | Arbitrary headers/query selector variants not exhaustively tested |
| X02 | Foreign document read | Both directions denied in supplied HTTP report and in-memory tests | Full concurrent and multi-process conditions |
| X03 | Foreign update | Two-direction reindex denial in supplied HTTP report | Concurrency/TOCTOU analysis |
| X04 | Cross-tenant vector search | Tenant-scoped search in supplied HTTP report | Quality of semantic search; adversarial unfiltered privileged calls |
| X05 | Foreign deletion | Two-direction denial in supplied HTTP report | Race conditions, privileged Qdrant access |
| X06 | Reindex ownership | Foreign update denial and owner updates in HTTP report | Mixed bulk reindex not implemented |
| X07 | Missing/invalid identity | 401 in in-memory and HTTP checks | Real credential lifecycle not implemented |
| X08 | Docker/Qdrant reachability | Compose declares `127.0.0.1:6333` bind | Host network inspection not independently supplied |
| X09 | Response metadata | HTTP report verified tenant IDs and own contents | Broader payload/error leak audit |
| X10 | Shared vs per-tenant | Prior supplied TestClient live-smoke evidence reports PASS for each | Independently asserted real-HTTP run for both strategies |
| X11 | Evidence hygiene | Publication package scanned; internal evidence excluded | Independent scans of original Windows workspace and service logs |
| X12 | Clean rebuild | Python tests rerun from isolated extracted package | Docker image/pip lockfile and clean Qdrant rebuild not rerun here |

**Evidence classifications:** "independently rerun" = executed during publication audit; "supplied report" = artifact checked but not reproduced; "unverified" = HOLD. These distinctions must persist in portfolio statements.
