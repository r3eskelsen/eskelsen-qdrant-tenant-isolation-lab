# G0 Threat Model

## Assets
Tenant vectors, synthetic document IDs, metadata and deletion/indexing rights; authorization decision; Qdrant service connection and API configuration.

## Adversaries
Untrusted tenant A client attempting to inspect tenant B resources; client capable of forging IDs, query parameters, JSON filters, or tenant headers; accidental programmer omission of tenant filter; accidental misconfigured Docker networking. Out of scope: compromised host OS, privileged operator, Qdrant administrator, malicious code dependency, credential theft outside the lab.

## Trust boundaries
HTTP client -> FastAPI authentication -> trusted tenant context -> repository authorization -> Qdrant. Only the trusted tenant context may determine scope. Qdrant network and storage are not exposed to arbitrary clients.

| Risk ID | Threat | Impact | Required mitigation | Adversarial test |
|---|---|---|---|---|
| T01 | Client forges `tenant_id` in body/query/header | Cross-tenant disclosure | Ignore/reject client-owned tenant selector | X01 |
| T02 | Client guesses B's document point ID | Disclosure or overwrite | Tenant-scoped lookups and mutation guards | X02/X03 |
| T03 | Repository search omits filter | Cross-tenant vector matches | Central mandatory filter construction | X04 |
| T04 | Delete by ID lacks authorization | Foreign tenant deletion | Check ownership and conditional tenant-scoped operation | X05 |
| T05 | Reindex operation copies foreign data | Cross-tenant indexing | Tenant-scoped source and destination | X06 |
| T06 | Unauthenticated/invalid identity | Unauthorized operation | Fail-closed identity resolution | X07 |
| T07 | Qdrant port reachable externally | Bypass FastAPI controls | Bind to loopback, restrict container network | X08 |
| T08 | Hidden foreign payload in response | Metadata leakage | Tenant-checked response shaping | X09 |
| T09 | Collection-name manipulation | Cross-tenant operations | Server-side allowlisted mapping | X10 |
| T10 | Configuration/logs expose synthetic tokens or secrets | Disclosure | Redacted evidence, no real credentials | X11 |

## Residual risks
Application bug, shared administrative credentials, direct database access, malicious insiders and supply chain compromise remain possible. Tests prove only the cases and environment actually measured.
