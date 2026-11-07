# G0 Architecture and Isolation Policy

## Objective and scope
Independent, reproducible, CPU-first local proof of tenant isolation in a vector retrieval API. Synthetic tenant identities and synthetic fixed-dimensional vectors only. The goal is authorization correctness, not quality benchmarking. Components proposed: FastAPI service, Qdrant local container (after isolated G1 approval), integration test runner, and optional in-memory unit-test adapter.

## Data path
1. Test client authenticates using a synthetic, server-configured identity. Credentials are only for isolated local tests.
2. Authentication resolves an immutable `tenant_id` server-side. Reject missing, invalid, or ambiguous identity with 401/403.
3. Service authorizes a document operation using the trusted tenant context; never accept arbitrary tenant selection from client payload, headers, query filters, or IDs.
4. Repository layer constructs the Qdrant filter using the trusted tenant ID for every read, search, update, delete, scroll, and reindex operation.
5. Response shaping excludes internal tenant identifiers and foreign point metadata where not necessary.

## Proposed primary layout
A **shared collection** with `tenant_id` as an indexed payload field. Every operation MUST include a server-generated tenant filter; direct Qdrant access must remain inaccessible to lab clients. Stable point identifiers must not confer authorization. Use an explicit repository layer as the single Qdrant access boundary. Test no-filter and forged-filter adversarial cases. Set a deterministic similarity threshold during G2 and log the value; note it is not an authorization mechanism.

## Alternative to compare
**Collection per tenant:** server maps trusted tenant identity to allowlisted collection name. Isolation can reduce accidental cross-tenant query risk, but increases collection management and does not protect against incorrect collection mapping, privileged Qdrant access, or identity compromise. Neither design is an absolute guarantee.

| Dimension | Shared collection + mandatory filter | Collection per tenant |
|---|---|---|
| Authorization boundary | Trusted server + enforced query filter | Trusted server + enforced collection mapping |
| Operational complexity | Lower collection count | Higher lifecycle/collection count |
| Misconfiguration risks | Filter omission, unscoped point operations | Cross-tenant collection selection/mapping |
| Evaluation | Negative search, get, update, delete, scroll/reindex | Repeat same negative tests, inspect mapping |

## Lab network contract
Do not publish Qdrant or API to 0.0.0.0 by default. Prefer localhost-only published ports, an isolated named Docker network, dedicated project volumes and unprivileged processes. Check port ownership, project labels, Docker context, available RAM, image provenance, and host capabilities in G1 before starting containers.

## Design guardrails
Never reuse real client data or production code. No real-world authentication guarantees from synthetic keys. No external model/API dependencies. Read-only G1 does not make network/container changes. Container start, pull, volume creation and firewall modifications require a later explicit G2 execution step.

## Proposed performance measurements
Report dataset size per tenant, retrieval count, unauthorized results, test repetitions, API error rates, vector dimension, engine versions and measured latency only after actual runs. Zero leakage is acceptance for the tested cases, not a security certification.
