# Test strategy

What will be tested, why, how, when, and with which resources. Tests only pay off inside a **strategy**; prefer TDD during Construction over a dump at the end of the cycle.

Levels (component, integration, system, acceptance), types (functional vs non-functional), and techniques (black-box, white-box, exploratory) follow common industry practice. *Manual vs automatic* is how tests are **executed**, not a quality type.

| Field | Value |
| --- | --- |
| Product | fastapi_rbac |
| Strategy version | 0.1 |
| Date | 2026-09-16 |
| Cycle / iteration | 4 phases, 6 weeks, 240 h; Construction is **TDD** (`FR-31`). This strategy’s **execution budget** is the Testing phase (1.5 weeks, 60 h). |
| Authors | John Guerrero |
| Sources | [Architecture-vision.md](Architecture-vision.md) (O1–O4, R1–R7, VC-001–VA-001); [Requirements.md](Requirements.md) (FR, NFR, AC, HTTP matrix); [README.md](README.md) |

---

## 1. Application under test

**Test object** and **test basis**. Verification (built right) and validation (right product) trace to architecture, requirements, and quality scenarios. Diagrams in 1.5–1.8 are the artifacts analysis and design derive cases from.

### 1.1 Application name

fastapi_rbac

### 1.2 Version

0.1 (cycle MVP: login, hybrid RBAC, self vs all-users CRUD, init CLI, SQLite default).

### 1.3 Description

fastapi_rbac is a FastAPI identity and access service. People authenticate with username/password over HTTPS JSON; the service issues an HS256 JWT whose claims include `sub` (user id), `role` (`user` or `admin`), and effective `permissions`. Administrators CRUD all users and grants; a caller with role `user` CRUD only their own row. Operators bootstrap the store from a **terminal** init CLI (not an unauthenticated HTTP register). Peer applications authorize from the token with the shared secret and do not call this product on their hot path.

### 1.4 Core functionalities and components to test

Runtime components from **VF-001**. There is no product web or mobile GUI; the channel under test is the HTTP JSON API plus the Init CLI.

| Capability / journey | Components under test | Channels | Notes (MVP vs later) |
| --- | --- | --- | --- |
| J-0 Initialize | Init CLI, Relational adapter | Terminal | MVP. Schema, seed `{user, admin}`, default permission catalog, first admin. |
| J-1 Login | HTTP API, Token issue, Identity check, Relational adapter | HTTPS JSON | MVP. One credential read; 200 with `access_token` + `user_id`. |
| J-2 Authorize | HTTP API, Token verify | HTTPS JSON | MVP. 0 store hops; 401 / 403 / 404. |
| J-3 Admin user | HTTP API, User and role administration, Relational adapter | HTTPS JSON | MVP. CRUD **all** users. |
| J-4 Hybrid grants | User and role administration, Identity check, Token issue | HTTPS JSON | MVP. Role grants ∪ extra user grants in next login. |
| J-5 Self profile | HTTP API, Token verify | HTTPS JSON | MVP. Own row only; other `{id}` → 404. |
| Health | HTTP API | HTTPS JSON | MVP. `GET /health` without token; no DB ping required. |
| Peer trust (O3) | Token verify (same secret, no HTTP to this product) | In-process JWT | MVP as a **function/contract** test, not a second deployed API. |

### 1.5 Architecture diagram

Pointer to the **component / functional** view testers will use to place unit, module, and integration tests. Prefer a link if the diagram is large.

**See:** [docs/diagrams/uml-components.png](docs/diagrams/uml-components.png), [docs/diagrams/uml-containers.png](docs/diagrams/uml-containers.png); Lucid [building blocks](https://lucid.app/lucidchart/d9604080-5380-4a18-8964-eea7faf66d35/edit), [containers](https://lucid.app/lucidchart/b7de0d28-4aff-4a3a-9d0b-d67e8c5bc42f/edit). Sequences: [login](docs/diagrams/seq-login.png), [authorize](docs/diagrams/seq-authorize.png), [init](docs/diagrams/seq-init.png).

This view must make evident **where SQL is allowed** (login, admin writes, init) versus **where it is forbidden** (authorize: Token issue/verify only). Unit tests sit on Token verify and hybrid-union; integration tests sit on HTTP API + adapter; CLI tests sit on Init CLI → adapter.

### 1.6 Context diagram

Pointer to the **context** view: actors, channels, and **external systems** that will need doubles, stubs, or contract tests.

**See:** [docs/diagrams/c4-context.png](docs/diagrams/c4-context.png); Lucid [Architecture p.1](https://lucid.app/lucidchart/ce9220eb-71a9-462a-b15e-343d00728c1f/edit); vision **VC-001**.

External system: **relational identity store** (SQLite file by default; PostgreSQL/MySQL via `DATABASE_URL`). Tests use an isolated SQLite file or `:memory:` as the default double of that store. PostgreSQL appears only in experiment **PR-03 / PI-02** (portability smoke). There is no IdP, broker, or gateway to stub.

### 1.7 Data model

Pointer to the **domain / information** view used for valid/invalid data scenarios (entities, states, ownership).

**See:** [docs/diagrams/data-model.png](docs/diagrams/data-model.png); Lucid [User RBAC](https://lucid.app/lucidchart/630829d8-5ce5-4bb5-b3f2-fffba2934f9d/edit); vision **VD-001**; Requirements §4–§5.

Valid: User \* — 1 Role; `name ∈ {user, admin}`; unique username/email; default catalog on `roles_permissions`; extra grants on `users_permissions`. Invalid: third role name, missing `role_id`, duplicate grants, password/hash in API bodies. Ownership: `admin` any User row; `user` only `id` = token `sub`.

### 1.8 GUI model

How presentation is structured. This product has no GUI to cover with visual or usability tests.

**See:** no product GUI and no HTML mockups. FastAPI `/docs` (OpenAPI) is a developer aid, not a visual-regression or usability target. All functional oracles are **HTTP status + JSON** (and CLI exit codes).

---

## 2. Scope of this test iteration

This cycle’s objectives, schedule, resources, approach, project risks, and **entry / exit / suspension** criteria. Not a master test plan for the product’s whole life.

### 2.0 Overall style

**TDD during Construction** (`FR-31`), plus a dedicated Testing phase for matrix gaps and architecture experiments. Not a dump of tests at the end of the cycle.

For every AC in Requirements §8: write a **failing** pytest named from that id → implement the minimum production code → **refactor** with the suite green. The Testing phase **re-runs** that suite, closes coverage on the HTTP matrix, and runs experiments.

**Gherkin is out of scope (`FR-33`).** Section 8 already is Given / When / Then. `.feature` files plus Behave/Cucumber/pytest-bdd would be a second source of truth for a solo Python API. pytest functions **are** the executable scenarios.

**Independence of testing:** John Guerrero is both developer and tester. Mitigation: oracles are the numbered AC *before* implementation; TDD forbids inventing tests after the code is already green.

Test process for this cycle:

| Process step | When |
| --- | --- |
| Planning & control | This document (Analysis / Design); control in Testing week |
| Analysis & design | AC-FR-\* / AC-NFR-\* as test conditions; decision table = Requirements §4.3 |
| Implementation & execution | Construction (**TDD** red → green → refactor); Testing (full matrix, CLI, experiments) |
| Evaluating exit criteria & reporting | End of Testing phase: coverage report + experiment verdicts in the repo |
| Closure | Archive pytest suite as regression; no separate QA handover |

**TDD is required for every AC** (`FR-31`), not only the high-risk slices. Exploratory time in Testing does not replace a missing red test.

### 2.1 Objectives

What this iteration should **achieve**. Each objective appears in the levels/types table (section 2.4).

- **OBJ-1** Isolate hybrid RBAC domain rules once: exactly two roles, effective permissions = role grants ∪ extra grants, no third role (AC-FR-14, AC-FR-21, AC-FR-21a).
- **OBJ-2** Defect-find on the **authorize** path: 0 identity-store round trips; decisions from token claims only (NFR-01, AC-FR-11, R1).
- **OBJ-3** Automate the HTTP operation matrix: 401 / 403 / 404 / 409 / 422 with **identical public bodies** per status (AC-FR-09, AC-FR-10, AC-FR-10a–d).
- **OBJ-4** Prove login: one credential read; `user_id` in JSON equals JWT `sub`; unknown user and wrong password share one 401 (AC-FR-01, AC-FR-03, AC-FR-07).
- **OBJ-5** Security oracles without a pentest: no existence leak (404 not 403 for other `{id}`), no password/hash in responses, JWT fail-closed, `JWT_SECRET` not in the image (NFR-05, NFR-06, NFR-09, R5, R7).
- **OBJ-6** Init CLI: empty store → admin can log in; custom `DATABASE_URL` honored; idempotent second run; fail-closed without `JWT_SECRET` (AC-FR-24, AC-FR-25, AC-FR-28, AC-FR-29).
- **OBJ-7** Peer trust: a verifier that shares `JWT_SECRET` accepts a token with **0** HTTP calls to this product (O3, FR-12).
- **OBJ-8** Portability smoke: same tests against PostgreSQL via `DATABASE_URL` (NFR-03, AC-NFR-03) — not a load test.

### 2.2 Duration of the test iteration

Cycle is **6 weeks / 4 phases**. Columns below are those phases (1.5 weeks each). **Execution hours** are the Testing column (60 h). Strategy and framework design sit in Analysis/Design (already budgeted in the vision, not double-counted here).

| Task | Analysis | Architecture design | Construction | Testing |
| --- | --- | --- | --- | --- |
| Test strategy design | This document | Refine vs VF-001 | — | Control / update if AC change |
| Test framework definition | pytest + TestClient chosen | Fixtures, env isolation | Implement `tests/` | CI job |
| Unit tests | AC as oracles | Fixture design | **TDD:** red pytest then code | Gap-fill + regression |
| Integration / contract | — | — | HTTP + SQLite | Init CLI + peer JWT |
| E2E / GUI | — | — | — | HTTP journeys only (no GUI) |
| Architecture experiments | Name PR/PS/PI | Instrumentation design | Hooks (query counter) | Run + verdict |
| Result analysis | — | — | — | Coverage + report |

Testing-phase calendar (indicative): **days 1–2** unit gap-fill and CI; **days 3–5** HTTP matrix + CLI; **days 6–8** experiments (0 hops, leak, image, Postgres); **days 9–10** analysis and exit report.

### 2.3 Test budget

**60 h** — vision Testing phase. No hired money. Unit-test *authoring* during Construction is paid from the Construction 60 h, not from this 60 h.

#### 2.3.1 Human resources

Prior testing experience, role in this iteration, available hours, optional hourly rate.

| Person | Role in testing | Hours | Rate (optional) | Total (optional) |
| --- | --- | --- | --- | --- |
| John Guerrero | Test designer, implementer, executor, reporter (solo) | 60 | N/A | N/A |
| **Total** | | **60** | | **N/A** |

#### 2.3.2 Computing resources

Laptops, emulators, devices, cloud, recorders. Note infrastructure **constraints** (e.g. cloud-first, no production load).

| Resource | Hours / notes | Cost |
| --- | --- | --- |
| Development laptop | pytest, coverage, uvicorn, SQLite | $0 (owned) |
| Docker Engine (local) | Postgres 16 for AC-NFR-03; image scan for AC-NFR-05 | $0 |
| CI (when repo has a pipeline) | Same suite as local; no production URL | $0 (GitHub/GitLab free tier if used) |

**Constraint:** no load against a shared or production database; no paid device lab; no cloud vendor is chosen (VA-001).

#### 2.3.3 Economic resources for hired services / extra staff

N/A. No outsourced QA, pentest firm, or performance lab this cycle.

### 2.4 Levels, types, and techniques

Map **how** you test to the objectives in 2.1.

| Term | Meaning in this document |
| --- | --- |
| **Level** | Component (unit), integration, system, acceptance |
| **Type** | *What* is evaluated: functional vs non-functional (performance, reliability, usability, security, maintainability, portability, compatibility). Manual vs automatic is **execution**, not a type |
| **Technique** | *How* cases are designed: black-box (equivalence partitioning, boundary values, decision tables, state transition, use case); white-box (statement / branch coverage); experience-based (exploratory, error guessing) |

Tools wait until section 4. **Regression** = re-run the full pytest suite after every fix. No separate commercial tool.

| Level | Type | Execution | Technique / experiments | Objectives (2.1) |
| --- | --- | --- | --- | --- |
| Component | Functional | Automatic | Equivalence partitioning + boundary values on credentials; decision table for hybrid union; branch coverage on Token verify | OBJ-1, OBJ-4 |
| Component | Functional | Automatic | White-box: authorize function never calls the session factory (monkeypatch / query counter = 0) | OBJ-2 |
| Integration | Functional | Automatic | Interface tests: FastAPI `TestClient` + SQLite; use-case J-1/J-3/J-5 | OBJ-3, OBJ-4 |
| Integration | Functional | Automatic | CLI as interface: `python -m app.cli init` subprocess against a temp URL | OBJ-6 |
| Integration | Functional | Automatic | Contract: peer verifier decodes HS256 with the same secret, 0 HTTP (FR-12) | OBJ-7 |
| System | Functional | Automatic | Decision table = Requirements §4.3 HTTP matrix; pytest Given/When/Then = AC-FR-\* | OBJ-3, OBJ-5 |
| Acceptance | Functional | Automatic | AC-FR-01…AC-FR-29 as named tests; no GUI UAT (API product) | OBJ-1–OBJ-6 |
| System | Non-functional — performance | Automatic | **PR-01**: 0 store/network hops on authorize (architectural SLO, not p95 ms) | OBJ-2 |
| System | Non-functional — security | Automatic | **PS-01–PS-03**: leak 404, fail-closed JWT, secret not in image | OBJ-5 |
| System | Non-functional — portability | Automatic | **PI-02**: `DATABASE_URL` → Postgres, login still works | OBJ-8 |
| System | Functional | Manual (light) | Error guessing / 1–2 h exploratory on OpenAPI only if automation gaps appear | OBJ-3 |

No usability, visual regression, i18n, random, or mutation testing this cycle (see 2.7).

### 2.5 Effort distribution

Assign **budget hours** (2.3) to **activities** (2.4), by capability and person. Totals must match 2.3.

| Capability | Task | Hours | Owner |
| --- | --- | --- | --- |
| Hybrid RBAC / token | Unit tests (union, two roles, claims, hash never returned) | 10 | John Guerrero |
| Authorize hot path | Unit + instrumentation (0 DB hops) | 6 | John Guerrero |
| HTTP matrix J-1–J-5 | Integration / system (TestClient, AC-FR-09–10d, 14, 16) | 12 | John Guerrero |
| Init CLI J-0 | Integration (AC-FR-24–29) | 6 | John Guerrero |
| Login + user_id | Integration (AC-FR-01, 03, 07) | 4 | John Guerrero |
| Default catalog | Data validation (AC-FR-21a, uniqueness) | 4 | John Guerrero |
| Peer JWT | Contract (FR-12) | 2 | John Guerrero |
| HTTP journeys | E2E-style pytest (login → me → admin CRUD) — not GUI | 4 | John Guerrero |
| Architecture experiments | PR-01, PS-01–03, PI-02 | 8 | John Guerrero |
| Exploratory | OpenAPI / error guessing (residual) | 2 | John Guerrero |
| GUI / visual regression | — | 0 | — |
| Analysis | Coverage, experiment verdicts, exit report | 2 | John Guerrero |
| **Total** | | **60** | |

### 2.6 Automation guidelines

Rules so scripts do not become technical debt. One **test case** has one oracle; a **scenario** is a procedure; the **suite** is `tests/`.

1. One pytest function = one oracle. Name tests after AC ids (`test_ac_fr_10a_other_user_is_404`). Do not assert five unrelated statuses in one function.
2. HTTP scenarios follow AC Given-When-Then. Fixtures build users/roles; tests do not share a dirty SQLite file across cases (temp DB or transaction rollback per test).
3. No `time.sleep()`. JWT expiry cases use a clock fixture or a token minted with `exp` in the past.
4. Secrets in tests are **test-only** values in env fixtures, never production `JWT_SECRET`. `.env` is not read by CI.
5. Authorize tests must fail if a DB session is opened for the **decision** (query counter / forbidden mock). Loading the row *after* allow is permitted and asserted separately.
6. Compare public error `detail` as an exact string per status (401/403/404), so a leak cannot hide behind a “helpful” message.
7. Do not hit the network except optional local Docker Postgres for PI-02. No third-party IdP.
8. The suite (`tests/`) is the regression pack: green before merge; confirmation test = the failing AC plus the suite (`FR-34`).
9. **TDD:** do not add production behavior for an AC until `test_ac_fr_*` fails for the right reason, then passes. Do not “write the test after it already passes” except to close a documented gap in the Testing phase.
10. **No Gherkin.** Do not add `*.feature`, Behave, Cucumber, or pytest-bdd (`FR-33`). Given / When / Then lives in Requirements §8 and in pytest names/docstrings.

### 2.7 Negative scope (out of this iteration)

What you will **not** test now.

- Product GUI, visual regression, accessibility, or usability labs (no presentation channel).
- OAuth2 / OIDC, refresh tokens, MFA, email verify, password reset (out of product scope).
- Numeric **p95 latency** SLO (not specified; NFR-01 is hop-count, not milliseconds). No Locust/k6 soak against production.
- Paid penetration test, OWASP ZAP full crawl, or regulator certification.
- Multi-writer SQLite correctness (NFR-04 says use a server RDBMS; we do not prove SQLite locking).
- MySQL smoke (Postgres is the portability representative this cycle).
- Mutation testing, random/monkey, i18n/l10n.
- Gherkin `.feature` files and a second BDD runner (`FR-33`). Requirements §8 is the GWT spec.
- Independent peer application as a second deployed service (peer trust is the in-process verifier).
- Public self-registration (admin-provisioned only).

### 2.8 Risks

**Product risks** (quality attributes that can fail in the live system) vs **project risks** (this strategy cannot be executed). Product risks trace to vision R1–R7 and NFRs.

| Kind | Risk | Probability | Impact | Handling |
| --- | --- | --- | --- | --- |
| Product | R1 — authorize hits the store → O1 fails | Medium | High | PR-01 query-counter tests; white-box unit on Token verify (OBJ-2) |
| Product | R2 — third role name accepted | Low | High | AC-FR-14; seed-only catalog assertion (OBJ-1) |
| Product | R3 / O3 — peers must call this API to learn role | Medium | High | PI-01 in-process verify, 0 HTTP (OBJ-7) |
| Product | R4 — login N+1 queries | Medium | Medium | AC-FR-07 query count on login (OBJ-4) |
| Product | R5 — `JWT_SECRET` in image or git | Medium | High | PS-03 filesystem scan of built image; `.gitignore` (OBJ-5) |
| Product | R6 — no first admin / init deadlock | Medium | High | AC-FR-24–29 CLI tests (OBJ-6) |
| Product | R7 — 403 on other `{id}` leaks existence | High | High | PS-01 / AC-FR-10a same body whether B exists or not (OBJ-5) |
| Product | NFR-06 — invalid JWT yields 200 | Low | High | Equivalence classes: missing, malformed, expired, bad signature → 401 |
| Project | Solo tester = same person as developer | High | Medium | Oracles frozen in Requirements.md before code; AC ids in test names |
| Project | Postgres lab missing (Docker down) | Medium | Low | Mark PI-02 `skipif` no Docker; SQLite remains the default suite; do not skip PR-01/PS-01 |
| Project | Construction slips → Testing starts without TestClient suite | Medium | High | Entry criterion 2.9; suspend rather than invent manual-only matrix |
| Project | Flaky JWT expiry tests | Medium | Low | Frozen clock fixture (guideline 2.6.3) |

### 2.9 Entry, suspension, and exit criteria

**Entry criteria** (ready to start), **suspension / resumption**, and **exit criteria** (done enough to stop). Exit is not “zero defects”; it is the agreed evidence for this iteration.

**Entry (start Testing-phase execution when):** Requirements.md AC set is stable; Construction has `POST /auth/login`, Bearer auth, users CRUD, and `python -m app.cli init` callable; `JWT_SECRET` injectable in test env; SQLite temp path works; pytest collects a non-empty suite.

**Suspend if:** login or init is blocking (cannot obtain a token or seed an admin); authorize always opens a DB session (PR-01 cannot even instrument); Docker image build is required for PS-03 but Dockerfile is absent and Construction is not complete.

**Resume when:** the blocking FR has a confirmation test green; query-counter hook exists; image can be built without baked secrets.

**Exit (iteration complete when):**

- All AC-FR-\* and AC-NFR-05 automated and green on SQLite (AC-NFR-03 green **or** skipped with documented Docker absence).
- HTTP matrix §4.3 covered for unauthenticated / `user` / `admin`.
- PR-01, PS-01, PS-02 recorded with pass/fail; PS-03 run if an image exists.
- Branch coverage target on Token verify + permission check: **≥ 80%** (not a whole-repo vanity number).
- Short test report in the repo (pytest summary + experiment table).
- Suite is the regression pack for later changes.

---

## 3. Test types and experiments

Functional and non-functional characteristics. Each experiment is a **test condition** with an **oracle** (expected response / measure). Pick only what this cycle needs.

| ID | Quality attribute | Traces to | Type |
| --- | --- | --- | --- |
| PR-01 | Authorize latency (0 store hops) | O1, NFR-01, AC-FR-11, R1 | Performance (architectural, not p95) |
| PS-01 | Confidentiality / existence leak | O2, NFR-09, FR-10a, AC-FR-10a, R7 | Security |
| PS-02 | Integrity of tokens | NFR-06, FR-09 | Security |
| PS-03 | Secret hygiene | NFR-05, AC-NFR-05, R5 | Security |
| PI-01 | Peer integrability (shared secret) | O3, FR-12 | Contract |
| PI-02 | Store portability | NFR-03, AC-NFR-03, AC-FR-25 | Portability |

### 3.1 Performance and scalability

**ID:** PR-01  
**Associated stories:** O1, NFR-01, AC-FR-11, VF-001 authorize sequence  
**Objective:** Evidence that allow/deny uses only the signed token — **0** identity-store round trips on the authorize path.  
**Preconditions:** App started with a query counter or session factory spy; valid admin (or user) JWT; SQLite or any store.  
**Stimulus:** `GET /users` (admin) or `GET /users/me` (user) — protected route. Repeat for 401 (no header) and 403 (`user` + `GET /users`).  
**Expected response / measure:** For the **authorization decision**, store round trips = **0**. After allow, listing/loading rows may use SQL; that count is recorded separately and must not be mixed into the authorize metric. No millisecond p95 is in scope.  
**Associated technologies:** FastAPI, Token verify, pytest spy / SQLAlchemy event `before_cursor_execute`.  
**Interpretation:** Fail = R1 realized; architecture is not the claimed hot path. Pass = O1 satisfied for this cycle.  
**Effort:** 3 h — John Guerrero

### 3.2 Resilience / reliability / channel (e.g. offline)

None this cycle. Health is functional (`GET /health` without DB ping, NFR-08), covered as an acceptance test, not a chaos experiment.

### 3.3 Security

**ID:** PS-01  
**Associated stories:** FR-03, FR-10a, NFR-09, AC-FR-03, AC-FR-10a, R7  
**Objective:** Public HTTP codes must not filter whether a username, email, or user id exists.  
**Preconditions:** Seeded users A (`role=user`) and B; token for A. Second run with B **deleted**.  
**Stimulus:** Login with unknown username vs wrong password; `GET/PATCH/DELETE /users/{B}` as A.  
**Expected response / measure:** Login both cases HTTP **401** and **identical** `detail`. Cross-user object access HTTP **404** and **identical** `detail` whether B exists or not. Never 403 on `/users/{id}` for role `user`. Bodies contain no username, email, or “does not exist vs forbidden” distinction.  
**Associated technologies:** TestClient, pytest.  
**Interpretation:** Fail = existence leak (R7). Pass = NFR-09.  
**Effort:** 2 h — John Guerrero

**ID:** PS-02  
**Associated stories:** FR-09, NFR-06  
**Objective:** HS256 verify fails closed.  
**Preconditions:** `JWT_SECRET` set; one valid token minted.  
**Stimulus:** Missing header; `Bearer` malformed; expired `exp`; signature with a different secret.  
**Expected response / measure:** HTTP **401** in all cases, never 200.  
**Associated technologies:** PyJWT, TestClient, clock fixture.  
**Interpretation:** Fail = forged or stale token accepted.  
**Effort:** 1.5 h — John Guerrero

**ID:** PS-03  
**Associated stories:** NFR-05, AC-NFR-05, R5  
**Objective:** Signing secret is not baked into the container image.  
**Preconditions:** Docker image built from the repo Dockerfile; no `--build-arg JWT_SECRET`.  
**Stimulus:** Scan image filesystem / history / env defaults for the test secret string and for a baked `.env`.  
**Expected response / measure:** Secret string absent; runtime gets secret only from `env_file` / orchestrator.  
**Associated technologies:** `docker build`, `docker run --rm` with no env (app must refuse to serve without secret), optional `docker history`.  
**Interpretation:** Fail = R5. Skip only if Construction has not yet produced a Dockerfile (record in the report).  
**Effort:** 1.5 h — John Guerrero

### 3.4 Integration and API contracts

**ID:** PI-01  
**Associated stories:** O3, FR-12  
**Objective:** A peer can repeat FR-08–FR-11 using the same `JWT_SECRET` **without** calling this service.  
**Preconditions:** Token issued by login (or Token issue unit). Peer = a test module that only has the secret and PyJWT.  
**Stimulus:** Peer verifies signature, `exp`, reads `sub` / `role` / `permissions`; decides allow/deny for a sample route rule. Network to fastapi_rbac is blocked or unasserted (call count = 0).  
**Expected response / measure:** Valid token accepted; tampered token rejected; **zero** HTTP requests to the app.  
**Associated technologies:** PyJWT, pytest (no TestClient in this experiment).  
**Interpretation:** Fail = O3 not met (peers still coupled to the HTTP API).  
**Effort:** 1 h — John Guerrero

**ID:** PI-02  
**Associated stories:** NFR-03, AC-NFR-03, AC-FR-25, FR-25  
**Objective:** `DATABASE_URL` is honored; engine swap does not require application code changes beyond driver install.  
**Preconditions:** (a) temp SQLite path ≠ default `./rbac.db`; (b) optional local Postgres 16 via Docker Compose.  
**Stimulus:** `python -m app.cli init` with each URL; login with seeded admin.  
**Expected response / measure:** Schema and admin exist **at the given URL**; default file is not created in (a); login 200 in both.  
**Associated technologies:** Init CLI, SQLAlchemy, Docker Postgres.  
**Interpretation:** Fail = silent ignore of URL (FR-25) or SQLite-only coupling. Postgres skip if Docker unavailable (project risk 2.8).  
**Effort:** 3 h — John Guerrero (includes CLI AC-FR-24–29 overlap)

### 3.5 Modifiability (optional)

Omit as a separate experiment. Portability of the store is PI-02. Hybrid grants (J-4) are functional tests (AC-FR-21), not a separate modifiability goal.

### 3.6 Internationalization (i18n / l10n)

Omit. Public `detail` strings are English and must stay **stable** for leak tests; they are not localized this cycle.

### 3.7 Exploratory, GUI, data (optional)

- **Exploratory (2 h):** charter — “As `user`, try to observe another account via timing, verbose 422, or `/users?id=`.” Only if time remains after the matrix is green.
- **Data:** pytest fixtures / factories for User, Role, Permission; unique username/email pools. No generated million-row data.
- **GUI / visual regression / mutation / random:** not in the levels/types table.

---

## 4. Frameworks and environments

**Test environment** and **testware** (runners, scripts, data, doubles). Concrete tools chosen for this Python/FastAPI product.

### 4.1 Test framework (by kind)

| Kind | Tool | Justification |
| --- | --- | --- |
| Unit | pytest + coverage.py (branch) | Default Python stack; matches FastAPI docs; AC names as test ids |
| Integration / contract | FastAPI `TestClient` (Starlette) + SQLAlchemy SQLite temp/memory | In-process HTTP without a live port; store is the only external, replaced by a file double |
| CLI | pytest + subprocess (or Click runner if the CLI uses Click) | Init is a terminal command (FR-24), not HTTP |
| E2E | pytest functions named from AC Given-When-Then | Executable scenarios without Gherkin; `FR-33` forbids a second runner |
| Performance | SQLAlchemy event / session spy (PR-01) | SLO is **0 hops**, not a load generator |
| Security | Same pytest suite + `docker` for PS-03 | Leak and fail-closed are functional security tests |
| Visual regression | — | No GUI |
| i18n | — | Out of scope |

### 4.2 Framework for the web channel

No web channel. Do not add Playwright/Cypress. OpenAPI `/docs` is not automated.

### 4.3 Framework for the mobile channel

Out of scope.

### 4.4 Backend / cloud test environment

Where experiments run vs where functional tests run. Isolation, IaC, cost, destroy-after-run.

| Element | Definition |
| --- | --- |
| Compute | Developer laptop; uvicorn only when a human exploratory pass needs `/docs`. pytest uses TestClient (no separate server for the default suite). |
| Network | Loopback only. Peer experiment PI-01 must not require a second host. |
| Data / cache / bus | SQLite temp file or `:memory:` per test. No Redis, no broker (not in architecture). Optional Postgres container **destroyed after PI-02**. |
| Provisioning | `python -m app.cli init` in tests with fixture env (`JWT_SECRET`, `ADMIN_*`, `DATABASE_URL`). Docker Compose only for Postgres smoke. |
| Cost | $0. No cloud vendor (VA-001). |
| Test tools in that lab | pytest, coverage.py, Docker Engine (optional) |

**Constraint:** no load against production; no real `JWT_SECRET`; local development machine only. Fail closed if production-like URLs appear in test config.

---

## Traceability (strategy → spec)

| Strategy | Requirements / vision |
| --- | --- |
| OBJ-1, unit decision table | FR-13–FR-21a, AC-FR-14, AC-FR-21, AC-FR-21a |
| OBJ-2, PR-01 | NFR-01, AC-FR-11, R1, VF-001 authorize |
| OBJ-3, HTTP matrix | Requirements §4.3, AC-FR-09–10d |
| OBJ-4 | FR-01–FR-07, AC-FR-01, AC-FR-03, AC-FR-07 |
| OBJ-5, PS-01–03 | FR-03, FR-09, FR-10a, NFR-05, NFR-06, NFR-09 |
| OBJ-6, PI-02 (CLI) | FR-24–FR-30, J-0 |
| OBJ-7, PI-01 | FR-12, O3 |
| OBJ-8, PI-02 (Postgres) | NFR-03, AC-NFR-03 |
| TDD process, no Gherkin | FR-31–FR-34, AC-FR-31, AC-FR-33 |
| No GUI tests | VC-001: HTTPS JSON + terminal only |
