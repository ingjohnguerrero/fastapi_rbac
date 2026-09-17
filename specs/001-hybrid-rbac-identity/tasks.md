# Tasks: Hybrid RBAC identity

**Input**: Design documents from `/specs/001-hybrid-rbac-identity/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: MANDATORY (constitution III). Write `test_ac_*` so they **fail**, then implement. No Gherkin.

**Organization**: Setup → Foundational (blocks all stories) → user stories in spec priority order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel (different files, no incomplete dependencies)
- **[Story]**: [US1]…[US7] on story-phase tasks only
- Every task includes an exact file path

## Path Conventions

- Production: `app/` (`python -m app.cli init`, `uvicorn app.main:app`)
- Tests: `tests/unit/`, `tests/integration/`, `tests/contract/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Empty package layout and installable dependencies

- [X] T001 Create package tree `app/`, `app/api/`, `app/auth/`, `app/models/`, `app/services/`, `app/adapters/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `scripts/` with `__init__.py` files per `specs/001-hybrid-rbac-identity/plan.md`
- [X] T002 Write `requirements.txt` with FastAPI, uvicorn, SQLAlchemy 2.x, PyJWT, pwdlib[argon2], pydantic-settings, pytest, httpx, coverage
- [X] T003 [P] Write `.env.example` with `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_URL`, `ADMIN_*` per README
- [X] T004 [P] Write `pytest.ini` (`testpaths = tests`) and a stub `tests/conftest.py`

**Checkpoint**: `pip install -r requirements.txt` and `pytest` collect 0 tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings, store, models, token/hash primitives, test fixtures. No user-story HTTP yet except an empty FastAPI app.

**⚠️ CRITICAL**: No user story work until this phase is complete. Token modules MUST NOT import `app.adapters.db`.

- [X] T005 Write failing `tests/unit/test_settings.py` asserting missing `JWT_SECRET` fails closed
- [X] T006 Implement `app/settings.py` (pydantic-settings; default `DATABASE_URL=sqlite:///./rbac.db`, HS256, TTL 30) so T005 passes
- [X] T007 Write failing `tests/unit/test_hashing.py` for hash/verify and never-plaintext
- [X] T008 Implement `app/auth/hashing.py` (pwdlib Argon2) so T007 passes
- [X] T009 Write failing `tests/unit/test_tokens.py` for issue/verify, expired and bad-signature → fail closed, no database import
- [X] T010 Implement `app/auth/tokens.py` (PyJWT HS256 claims `sub`, `role`, `permissions`, `exp`, `iat`) so T009 passes
- [X] T011 Implement engine/session/`create_all` in `app/adapters/db.py` from `DATABASE_URL`
- [X] T012 Implement SQLAlchemy entities in `app/models/entities.py` (User, Role, Permission, `roles_permissions`, `users_permissions`) per `specs/001-hybrid-rbac-identity/data-model.md`
- [X] T013 Implement `app/auth/principal.py` (Bearer → Principal from claims only)
- [X] T014 Implement `app/auth/authorize.py` (permission names + `sub` vs `{id}` ownership; no session)
- [X] T015 Extend `tests/conftest.py` with temp SQLite, env fixtures, and SQLAlchemy `before_cursor_execute` query counter
- [X] T016 Implement empty FastAPI app in `app/main.py` (no business routes yet; lifespan must not require a DB ping)

**Checkpoint**: Unit tests for settings/hashing/tokens green; `uvicorn` can import `app.main:app`

---

## Phase 3: User Story 1 - First-time setup (Priority: P1) 🎯 MVP

**Goal**: Terminal init creates schema, seeds `{user, admin}` and the default catalog, inserts the first admin, honouring `DATABASE_URL`.

**Independent Test**: Empty store + `JWT_SECRET` + `ADMIN_*` → `python -m app.cli init` exit 0; admin can later sign in. Second run exit 0 without password change. Missing secret → non-zero, no admin.

### Tests for User Story 1 (REQUIRED — TDD)

- [X] T017 [US1] Write failing `tests/integration/test_ac_fr_24_init.py` covering AC-FR-24, AC-FR-25, AC-FR-28, AC-FR-29, AC-FR-21a

### Implementation for User Story 1

- [X] T018 [US1] Implement catalog seed in `app/services/seed.py` (roles, default permissions, `roles_permissions`)
- [X] T019 [US1] Implement `python -m app.cli init` in `app/cli.py` per `specs/001-hybrid-rbac-identity/contracts/init-cli.md`
- [X] T020 [US1] Implement `scripts/init.sh` wrapping `python -m app.cli init`

**Checkpoint**: `pytest tests/integration/test_ac_fr_24_init.py` green

---

## Phase 4: User Story 2 - Sign in and recover identity (Priority: P1)

**Goal**: `POST /auth/login` returns `access_token`, `token_type=bearer`, `user_id` equal to JWT `sub`; one credential read; identical 401 for unknown user and wrong password.

**Independent Test**: Seed a `user`; correct password → 200 with matching `user_id`/`sub`/`role=user`. Wrong password and unknown username share `detail: Unauthorized`.

### Tests for User Story 2 (REQUIRED — TDD)

- [X] T021 [US2] Write failing `tests/integration/test_ac_fr_01_login.py` covering AC-FR-01, AC-FR-03, AC-FR-07 (query count)

### Implementation for User Story 2

- [X] T022 [US2] Implement one-read login + permission union in `app/services/login.py`
- [X] T023 [US2] Implement `POST /auth/login` in `app/api/auth.py` (200/401/422 per `contracts/http-api.md`)
- [X] T024 [US2] Include auth router in `app/main.py`

**Checkpoint**: `pytest tests/integration/test_ac_fr_01_login.py` green

---

## Phase 5: User Story 3 - Later access from the signed proof (Priority: P1)

**Goal**: Protected routes use JWT only for allow/deny (0 store hops). Missing token 401; `user` listing people 403. Peer verifies with secret and 0 HTTP.

**Independent Test**: No header → 401 on `GET /users`. Valid `user` token → 403 on `GET /users`. Query counter 0 on authorize. Peer module accepts valid token, rejects tampered, no TestClient.

### Tests for User Story 3 (REQUIRED — TDD)

- [X] T025 [P] [US3] Write failing `tests/integration/test_ac_fr_09_authorize.py` covering AC-FR-09, AC-FR-10
- [X] T026 [P] [US3] Write failing `tests/unit/test_ac_fr_11_no_db.py` covering AC-FR-11 (0 sessions for the decision)
- [X] T027 [P] [US3] Write failing `tests/contract/test_peer_jwt.py` covering FR-12 / AC peer (0 HTTP)

### Implementation for User Story 3

- [X] T028 [US3] Implement `GET /users` in `app/api/users.py` (401 unauthenticated, 403 without `users:read`, 200 list for admin) using `app/auth/authorize.py` only for the decision
- [X] T029 [US3] Mount users router in `app/main.py`

**Checkpoint**: T025–T027 green; authorize path does not import a session for the decision

---

## Phase 6: User Story 4 - Administrator manages all people (Priority: P2)

**Goal**: Admin CRUD any user; unique username/email; only roles `user`|`admin`; list roles.

**Independent Test**: Admin create/list/patch/delete another user. `"role": "superadmin"` → 422/400 no row. Duplicate username → 409. Member `POST /users` → 403.

### Tests for User Story 4 (REQUIRED — TDD)

- [X] T030 [US4] Write failing `tests/integration/test_ac_fr_10d_admin_users.py` covering AC-FR-10d, AC-FR-14, AC-FR-16

### Implementation for User Story 4

- [X] T031 [US4] Implement user CRUD in `app/services/users.py` (unique 409, role catalog check, never return hashes)
- [X] T032 [US4] Extend `app/api/users.py` with `POST /users`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` for admin
- [X] T033 [US4] Implement `GET /roles` in `app/api/roles.py` and mount in `app/main.py`

**Checkpoint**: Admin HTTP matrix for users/roles green

---

## Phase 7: User Story 5 - Member manages only themselves (Priority: P2)

**Goal**: `user` CRUD own row (`/users/me` or `{id}=sub`); other ids **404** same body whether they exist; cannot set own role; list-all still 403.

**Independent Test**: As A, GET me and GET A → 200. GET B exists or not → 404 identical. PATCH email → 200; PATCH role admin ignored or 422. GET /users → 403.

### Tests for User Story 5 (REQUIRED — TDD)

- [X] T034 [US5] Write failing `tests/integration/test_ac_fr_10a_self.py` covering AC-FR-10a, AC-FR-10b, AC-FR-10c

### Implementation for User Story 5

- [X] T035 [US5] Extend `app/api/users.py` with `GET /users/me` and ownership 404 in GET/PATCH/DELETE; reject or ignore `role` on member PATCH

**Checkpoint**: Existence-leak tests green (404 not 403)

---

## Phase 8: User Story 6 - Extra permissions without a new role (Priority: P3)

**Goal**: Admin attaches role grants and extra user grants; next login token is union; role name unchanged; duplicate pairs rejected.

**Independent Test**: Role `user` + `items:read`, extra `items:write` → login `role=user` and both names. Duplicate grant rejected.

### Tests for User Story 6 (REQUIRED — TDD)

- [X] T036 [US6] Write failing `tests/integration/test_ac_fr_21_hybrid.py` covering AC-FR-21

### Implementation for User Story 6

- [X] T037 [US6] Implement grant attach in `app/services/grants.py`
- [X] T038 [US6] Implement `POST /roles/{id}/permissions` and `POST /users/{id}/permissions` in `app/api/roles.py` / `app/api/users.py` (admin `users:grant` / `roles:grant`)

**Checkpoint**: Hybrid union appears in JWT; no third role

---

## Phase 9: User Story 7 - Service liveness (Priority: P3)

**Goal**: `GET /health` 200 without token and without DB ping.

**Independent Test**: Call health with store unreachable or unconfigured; 200 `{ "status": "ok" }`.

### Tests for User Story 7 (REQUIRED — TDD)

- [X] T039 [US7] Write failing `tests/integration/test_ac_fr_22_health.py` covering FR-22 / NFR-08

### Implementation for User Story 7

- [X] T040 [US7] Implement `GET /health` in `app/main.py` with no database access

**Checkpoint**: Health green without a token

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Operator artifacts, remaining AC, regression

- [X] T041 [P] Add `Dockerfile` (uvicorn, no baked `JWT_SECRET`) at repo root
- [X] T042 [P] Add `docker-compose.yml` SQLite volume layout per README
- [X] T043 Write `tests/integration/test_ac_nfr_05_image.py` (skip if Docker missing) covering AC-NFR-05
- [X] T044 Write `tests/integration/test_ac_nfr_03_postgres.py` (`skipif` no Docker) covering AC-NFR-03
- [X] T045 Confirm no `*.feature` files (AC-FR-33); run full `pytest` and `specs/001-hybrid-rbac-identity/quickstart.md` locally

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: start immediately
- **Foundational (Phase 2)**: depends on Setup — **BLOCKS** all user stories
- **US1 → US2 → US3 → US4 → US5 → US6**: sequential on a solo cycle (login needs seeded admin; authorize needs login; CRUD needs authorize)
- **US7**: after Foundational; can run after US2 in parallel with US4–US6 if staffed
- **Polish**: after desired stories

### User Story Dependencies

- **US1 (P1)**: after Phase 2 only — MVP (init)
- **US2 (P1)**: after US1 (needs seeded admin/user)
- **US3 (P1)**: after US2 (needs tokens)
- **US4 (P2)**: after US3 (needs authorize + GET /users)
- **US5 (P2)**: after US4 (extends same `app/api/users.py`)
- **US6 (P3)**: after US2 (login union) and US4 (admin authz)
- **US7 (P3)**: after Phase 2; independent of CRUD

### Within Each User Story

- Tests MUST fail before implementation
- `app/auth/tokens.py` / `authorize.py` MUST NOT use the session factory
- Story green before the next priority on a solo schedule

### Parallel Opportunities

- T003, T004 after T001
- T025, T026, T027 after US2
- T041, T042 in Polish
- US7 tests/impl vs US4 if two people after US3

---

## Parallel Example: User Story 3

```bash
# After US2 is green, launch US3 tests together:
Task: "Write failing tests/integration/test_ac_fr_09_authorize.py"
Task: "Write failing tests/unit/test_ac_fr_11_no_db.py"
Task: "Write failing tests/contract/test_peer_jwt.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup
2. Phase 2 Foundational
3. Phase 3 US1 init CLI
4. **STOP**: empty store → init → first admin exists (login comes in US2)

### Incremental Delivery

1. Setup + Foundational
2. US1 init → demo bootstrap
3. US2 login → demo `user_id` + token
4. US3 authorize + peer verify
5. US4 admin CRUD
6. US5 self-only 404
7. US6 hybrid grants
8. US7 health
9. Polish (Docker, NFR tests, quickstart)

### Parallel Team Strategy

Solo cycle: follow priority order. If two people after Phase 2: A takes US1→US2→US3; B prepares US7 health after T016.

---

## Notes

- Map pytest names to Requirements.md AC ids (`test_ac_fr_10a_…`)
- Public error strings: `Unauthorized` / `Forbidden` / `Not found` / `Conflict`
- Avoid Gherkin, store hops on authorize, extra services
- Commit after each story checkpoint

**Counts**: 45 tasks (Setup 4, Foundational 12, US1 4, US2 4, US3 5, US4 4, US5 2, US6 3, US7 2, Polish 5)
