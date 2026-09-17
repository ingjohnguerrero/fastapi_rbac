# Implementation Plan: Hybrid RBAC identity

**Branch**: `001-hybrid-rbac-identity` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: [spec.md](./spec.md) plus product contract [Requirements.md](../../Requirements.md)

**Note**: Filled by `/speckit-plan`. Tasks are **not** in this command; use `/speckit-tasks`.

## Summary

Deliver a single FastAPI identity service that issues an HS256 JWT (`sub`, `role`, `permissions`) at login, authorizes later requests from that token with **0** store hops, and seeds hybrid RBAC (`user` | `admin`, role grants ∪ extra user grants). Operators bootstrap via `python -m app.cli init`. Construction is TDD against Requirements §8 AC ids. HTTP denials are 401 / 403 / 404 with identical public `detail` (no existence leak).

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: FastAPI, uvicorn, SQLAlchemy 2.x, PyJWT (HS256), pwdlib (Argon2), pydantic-settings

**Storage**: SQLite default (`sqlite:///./rbac.db`); PostgreSQL/MySQL via `DATABASE_URL` (SQLAlchemy URL)

**Testing**: pytest, FastAPI TestClient, coverage.py (branch); TDD required (`test_ac_fr_*` / `test_ac_nfr_*`)

**Target Platform**: HTTP JSON (uvicorn); terminal Init CLI

**Project Type**: web-service + CLI bootstrap

**Performance Goals**: Authorize path = 0 identity-store round trips (not a millisecond p95). Login = 1 credential read.

**Constraints**: Hybrid RBAC (`user`|`admin`); secrets from env; deny 401/403/404 without existence leak; no Gherkin; no gateway/cache/broker/IdP

**Scale/Scope**: Single process; SQLite colocated unless multiple writers (then server RDBMS)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-research and post-design: **all pass**. No Complexity Tracking rows.

- [x] **I. Token-First Authorize**: `app/auth/` verifies JWT in process; dependencies MUST NOT open a session for allow/deny (query-counter tests)
- [x] **II. Hybrid RBAC**: seed only `user` and `admin`; extra grants on `users_permissions`; union at login
- [x] **III. Test-First**: each Requirements AC has a failing pytest before production code; no Gherkin
- [x] **IV. Contract tests**: HTTP matrix, Init CLI / `DATABASE_URL`, peer verifier with 0 HTTP
- [x] **V. Simplicity**: one FastAPI process + Init CLI; SQLite default
- [x] **Security**: `JWT_SECRET` from env; hashes never in responses; cross-user object access is 404
- [x] **Layout**: `app/` and `tests/` as below

## Project Structure

### Documentation (this feature)

```text
specs/001-hybrid-rbac-identity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http-api.md
│   └── init-cli.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py                 # FastAPI app, health, routers
├── cli.py                  # python -m app.cli init
├── settings.py             # pydantic-settings from env
├── api/
│   ├── auth.py             # POST /auth/login
│   ├── users.py            # /users, /users/me, /users/{id}
│   └── roles.py            # GET /roles, grant routes
├── auth/
│   ├── tokens.py           # issue + verify HS256 (no store)
│   ├── hashing.py          # password hash/verify
│   ├── principal.py        # Bearer → Principal from claims
│   └── authorize.py        # permission + ownership (sub vs id)
├── models/
│   └── entities.py         # SQLAlchemy User, Role, Permission, grants
├── services/
│   ├── login.py            # one credential read + union permissions
│   ├── users.py            # CRUD after allow
│   └── grants.py           # role/user permission attach
└── adapters/
    └── db.py               # engine from DATABASE_URL, session factory

tests/
├── conftest.py             # temp SQLite, env, query counter
├── unit/                   # union, token verify, authorize (0 session)
├── integration/            # TestClient matrix, CLI subprocess
└── contract/               # peer JWT verify, 0 HTTP

scripts/
└── init.sh                 # thin wrapper around python -m app.cli init
```

**Structure Decision**: Single FastAPI package `app/` plus `tests/` (constitution V). Token verify lives in `app/auth/` and MUST NOT import the session factory. `adapters/db.py` is used only by login, admin writes, and init.

## Complexity Tracking

No constitution violations.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Phase 0 / Phase 1 artifacts

| Artifact | Path |
| --- | --- |
| Research | [research.md](./research.md) |
| Data model | [data-model.md](./data-model.md) |
| HTTP contract | [contracts/http-api.md](./contracts/http-api.md) |
| Init CLI contract | [contracts/init-cli.md](./contracts/init-cli.md) |
| Quickstart | [quickstart.md](./quickstart.md) |

Implementation order (for `/speckit-tasks`): settings + db → init CLI (US1) → login/token (US2) → authorize + health (US3, US7) → users CRUD (US4, US5) → grants (US6). TDD each AC from Requirements §8.
