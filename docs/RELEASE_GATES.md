# LAB-10 — Release Gate Status (2026-11-06)

The GitHub source **publication package** has passed static archive/file integrity review and an independent isolated in-memory pytest rerun. This does not imply that all original engineering/security acceptance gates have passed or that the repository is already hosted on GitHub.

| Gate | State | Reason |
|---|---|---|
| G0 — Architecture and scope | DOCUMENTED | Architecture, threat model and synthetic boundaries included. |
| G1 — Read-only host preflight | EVIDENCE GAP | Complete Windows host/Docker preflight evidence not in these materials. |
| G2 — Implementation | SOURCE AVAILABLE | API, Qdrant REST transport, tests and local Compose provided; running system not proven by static code alone. |
| G3 — Validation | PARTIAL PASS / HOLD | 2/2 local in-memory tests independently rerun. Owner-supplied reports show both live TestClient strategies and 44/44 real-HTTP checks, but not independently repeated; real-HTTP strategy unverified. |
| G4 — Source package publication QA | PASS | Public ZIP, MIT, manifest, static privacy audit; raw internal evidence excluded. |
| G5 — Upwork portfolio | READY AFTER GITHUB | Use only documented demo-level evidence and working public repository link; no production certification. |
| G6 — Market feedback | PENDING | Track profile views, proposals, interviews and actual contracts after publication. |

## Publication contract

Extract the ZIP before uploading the project files to GitHub. Place the **contents of the inner repository folder** at the repository root, including `README.md`, `LICENSE`, `src/`, `tests/`, `docs/`, `scripts/`, `.gitignore`, `.env.example`, `pyproject.toml`, and `compose.lab10.yml`.

Do not upload the ZIP itself as the only repository file, the original private evidence, local virtual environment, existing Docker volumes, API keys, `.env`, or credential files.

No repository push or public Upwork publication is claimed by this package. The owner performs and confirms those external steps.
