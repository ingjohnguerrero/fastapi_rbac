# Research: Hybrid RBAC identity

All Technical Context items are resolved from [Requirements.md](../../Requirements.md), the constitution, and current library practice. No `NEEDS CLARIFICATION` remains.

## JWT claims and authorize path

- **Decision**: HS256 via PyJWT. Claims: `sub` (string of User.id), `role` (`user`|`admin`), `permissions` (list of names), `exp`, `iat`. Verify signature and `exp` in process. `user_id` in login JSON is the integer id; treat as equal to `sub`.
- **Rationale**: Constitution I, FR-04/FR-05, O1. String `sub` matches JWT conventions; equality is defined in Requirements §7.1.
- **Alternatives considered**: Asymmetric keys (closed by technology constraint). Cookie sessions (closed). Looking up role on every request (fails O1 / R1).

## Password hashing

- **Decision**: Argon2id via `pwdlib[argon2]`. Never return hash or plaintext.
- **Rationale**: One-way hash (FR-06). Argon2id is the current default for new Python services; pwdlib is the maintained successor to passlib.
- **Alternatives considered**: passlib+bcrypt (maintenance mode). Raw bcrypt (weaker memory-hard properties). Recoverable encryption (forbidden).

## ORM and schema creation

- **Decision**: SQLAlchemy 2.x mapped models. Init and first app boot create tables with `metadata.create_all` (or equivalent migrate). No Alembic required for v0.1. Engine from `DATABASE_URL`; default `sqlite:///./rbac.db`.
- **Rationale**: NFR-03 portability; FR-25/FR-26 honour the URL. Alembic adds migration files before the schema is proven.
- **Alternatives considered**: Alembic from day one (defer until a schema change lands). Raw sqlite3 (blocks Postgres swap). Redis/document store (closed).

## Settings

- **Decision**: pydantic-settings. Required: `JWT_SECRET`. Defaults: `JWT_ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`, `DATABASE_URL=sqlite:///./rbac.db`. Init also reads `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`. Fail closed if secret missing.
- **Rationale**: FR-23, FR-29, README env table. 30 minutes matches Requirements open point until a product owner sets TTL.
- **Alternatives considered**: python-dotenv only (weaker typing). Baking defaults into the image (fails NFR-05).

## HTTP stack

- **Decision**: FastAPI + uvicorn. JSON UTF-8. Error `detail` strings: `Unauthorized`, `Forbidden`, `Not found`, `Conflict`. 422 from validation.
- **Rationale**: Already chosen backend. Identical public bodies (NFR-09, Requirements §4.2).
- **Alternatives considered**: Flask/Django (closed). Distinct login error messages (existence leak).

## Authorization implementation

- **Decision**: FastAPI dependencies: (1) `get_principal` verifies JWT only; (2) `require_permission` / ownership check uses claims (`sub` vs path id) with **no** session. After allow, handlers may load rows. SQLAlchemy `before_cursor_execute` spy in tests for AC-FR-07 and AC-FR-11.
- **Rationale**: Constitution I and IV. Ownership from token does not need a store hop.
- **Alternatives considered**: Casbin (extra engine). Checking permissions in the database on each request (fails O1).

## Testing

- **Decision**: pytest + TestClient + temp SQLite. CLI tests via subprocess with fixture env. Peer contract tests import `app.auth.tokens` only (0 HTTP). Names `test_ac_fr_*`. No Gherkin.
- **Rationale**: FR-31–FR-34, Test-strategy.
- **Alternatives considered**: pytest-bdd / Behave (forbidden). Hitting a live port (slower, flakier).

## Packaging and Docker

- **Decision**: `requirements.txt` (or `pyproject.toml`) at repo root. Dockerfile runs uvicorn; secrets only via `env_file`. Optional Compose for Postgres smoke (AC-NFR-03).
- **Rationale**: README operator guide; AC-NFR-05 image scan.
- **Alternatives considered**: Baking `.env` into the image (forbidden).
