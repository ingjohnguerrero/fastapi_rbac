# fastapi_rbac

Identity and access service: username/password login, HS256 JWT, **hybrid RBAC** (exactly one role per user — `user` or `admin` — plus optional extra permission grants). Authorize is decided from the token (`sub`, `role`, `permissions`); it does not query the identity store.

`admin` CRUD all users. `user` CRUD only their own record (`user_id` from login / JWT `sub`). Deny responses are HTTP status codes only (401 / 403 / 404) and do not disclose whether another account exists.

Full contract: [Requirements.md](Requirements.md). Views: [Architecture-vision.md](Architecture-vision.md).

**Status.** This README is the operator guide for the implemented service (local run, env, Docker). Application source, `Dockerfile`, and Compose files land in Construction under **TDD** (red pytest per AC → code → refactor). Gherkin is not used.

---

## Tech stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Runtime | Python 3.12+ | |
| HTTP | FastAPI + uvicorn | JSON over HTTPS in deployment; HTTP is fine locally |
| Auth proof | JWT HS256 | Claims: `sub` (user id), `role`, `permissions`, `exp`, `iat` |
| ORM / SQL | SQLAlchemy | Engine selected by `DATABASE_URL` |
| Default store | SQLite | File `./rbac.db` if `DATABASE_URL` is unset |
| Optional store | PostgreSQL or MySQL | Same app; change the URL and install the driver |
| Secrets | Environment / `.env` | Never baked into the image or committed |
| Bootstrap | Init CLI | `python -m app.cli init` or `./scripts/init.sh` |
| Package | Docker | uvicorn in the container; secrets via env at boot |
| Tests | pytest (TDD) | One test per AC id; no Gherkin / Behave |

Out of scope for this product: OAuth2/OIDC, refresh-token rotation, MFA, Redis as identity store, API gateway.

---

## Prerequisites

- Python 3.12 or later (local run)
- Docker Engine + Compose v2 (container run)
- A signing secret you generate yourself (`JWT_SECRET`)

---

## Environment (`.env`)

Copy the example and fill secrets. Do **not** commit `.env`.

```bash
cp .env.example .env
```

| Variable | Required | Default | Used by |
| --- | --- | --- | --- |
| `JWT_SECRET` | **Yes** | — | App and init. Fail closed if missing. |
| `JWT_ALGORITHM` | No | `HS256` | Token sign/verify |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` (until a product owner sets it) | Token `exp` |
| `DATABASE_URL` | No | `sqlite:///./rbac.db` | App and init. Honored as given; never silently ignored. |
| `ADMIN_USERNAME` | First init only | — | Init: first administrator |
| `ADMIN_EMAIL` | First init only | — | Init: first administrator |
| `ADMIN_PASSWORD` | First init only | — | Init: hashed, never stored plaintext |

**`.env.example`**

```env
JWT_SECRET=replace-me-with-a-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Omit DATABASE_URL to use sqlite:///./rbac.db
# DATABASE_URL=sqlite:///./rbac.db
# DATABASE_URL=postgresql+psycopg://rbac:rbac@db:5432/rbac

ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=choose-a-strong-password
```

SQLite URLs are relative to the process working directory. In Docker, point the file at a mounted volume (see below).

---

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set JWT_SECRET and ADMIN_*

python -m app.cli init
# equivalent: ./scripts/init.sh

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Init creates or migrates the schema, seeds roles `user` and `admin`, seeds the default permission catalog, and inserts the first admin if none exists. If an admin already exists, init is idempotent (exit 0, password unchanged).

| Check | Command |
| --- | --- |
| Liveness | `curl -s http://127.0.0.1:8000/health` → `200` |
| Login | `POST /auth/login` with JSON `username` / `password` → `200` and `{ "access_token", "token_type": "bearer", "user_id" }` |
| OpenAPI | `http://127.0.0.1:8000/docs` |

`user_id` in the login body equals JWT `sub`. Use `Authorization: Bearer <access_token>` on later requests.

To use PostgreSQL or MySQL locally, set `DATABASE_URL` before init (example: `postgresql+psycopg://user:pass@localhost:5432/rbac`) and install the matching driver.

---

## Docker setup

The image runs uvicorn only. **`JWT_SECRET` and `DATABASE_URL` are not in the image.** Pass them at runtime (`env_file` or orchestrator secrets).

### SQLite (default)

Persist the database file on a volume so it survives container recreation:

```bash
docker compose up --build
```

Expected Compose shape (SQLite):

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DATABASE_URL: sqlite:////data/rbac.db
    volumes:
      - rbac-data:/data
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

volumes:
  rbac-data:
```

First boot (schema + first admin), then start the API:

```bash
docker compose run --rm api python -m app.cli init
docker compose up
```

Health: `curl -s http://127.0.0.1:8000/health`

### PostgreSQL

Use a server RDBMS when more than one writer process shares state. Example Compose overlay:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: rbac
      POSTGRES_PASSWORD: rbac
      POSTGRES_DB: rbac
    volumes:
      - pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rbac -d rbac"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://rbac:rbac@db:5432/rbac
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

volumes:
  pg-data:
```

```bash
docker compose run --rm api python -m app.cli init
docker compose up
```

Keep `JWT_SECRET` in `.env` or a secret store. Do not put it in the Dockerfile, Compose `image` labels, or git.

---

## Default permissions (seeded at init)

| Role | Users |
| --- | --- |
| `admin` | CRUD **all** users; list roles; attach grants |
| `user` | CRUD **own** row only (`GET /users/me` or `/users/{id}` when `id` = token `sub`). Other ids → **404**. List/create users → **403**. |

HTTP denials: missing/invalid token → **401**; disallowed operation (list-all, create, roles) → **403**; role `user` targeting another `{id}` → **404** (same body whether that id exists or not). Login failures (unknown user or wrong password) share one **401** body.

---

## Further reading

- [Requirements.md](Requirements.md) — FRs, default catalog, HTTP matrix, init CLI, acceptance criteria
- [Architecture-vision.md](Architecture-vision.md) — context, domain, UML components, UML deployment
- [Test-strategy.md](Test-strategy.md) — TDD in Construction; architecture experiments (0 DB hops, no existence leak). No Gherkin.
- [`.specify/memory/constitution.md`](.specify/memory/constitution.md) — non-negotiable principles (token-first authorize, hybrid RBAC, TDD)
- Diagrams: [docs/diagrams](docs/diagrams)
