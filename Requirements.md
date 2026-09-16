# fastapi_rbac — Requirements specification

| Field | Value |
| --- | --- |
| Product | fastapi_rbac |
| Version | 0.1 |
| Date | 2026-09-15 |
| Status | Draft |
| Authors | John Guerrero |
| Related | [Architecture-vision.md](Architecture-vision.md) |

This document specifies what the identity and access service must do so it can be implemented and tested. Authorization is **hybrid RBAC** (one role per user plus optional extra user permissions). Architectural views (VC-001, VD-001, VF-001, VA-001) live in the vision; this spec gives numbered requirements, the HTTP contract, and acceptance criteria.

---

## 1. Introduction

### 1.1 Purpose

Define functional and non-functional requirements for a FastAPI service that:

1. Authenticates people with username/password.
2. Issues a signed JWT whose claims include `sub`, `role` (`user` or `admin`), and `permissions`.
3. Lets administrators **CRUD all users**, the two-role catalog, **role permission grants**, and **extra user permission grants** (hybrid RBAC).
4. Lets a caller with role `user` **CRUD only their own** user record; they cannot request other users.
5. Lets the same service and **peer applications** authorize later requests **from the token alone** (no identity-store hop). `user_id` is returned at login and is JWT `sub`.
6. Can be initialized from a terminal on an empty store (connection URL, schema, first admin, default permission catalog).
7. Returns **HTTP status codes** on deny; bodies do not leak whether another user exists.

### 1.2 Scope

**In scope**

- Login and JWT issue/verify (HS256).
- **Hybrid RBAC:** roles `user` and `admin` only (exactly one role per user); permissions granted to a role; optional extra permissions granted directly to a user; effective rights = role grants ∪ extra user grants.
- **Default permission catalog** (section 4): `admin` CRUD all users; `user` CRUD self only.
- User administration (admin), including both kinds of permission grant; self-service profile for role `user`.
- First-time **initialization** via a terminal script (connection URL, schema, seed roles, default permissions, first admin).
- **TDD** during Construction: pytest named after AC ids; red → green → refactor (`FR-31`).
- Health check.
- SQLite as default relational store; other relational engines via `DATABASE_URL`.

**Out of scope**

- OAuth2 / OIDC authorization server, refresh-token rotation product, social login, SAML, LDAP/Active Directory.
- Non-relational system of record (document DB, Redis as identity store).
- Email verification, password-reset flows, MFA.
- API gateway, service mesh, or dedicated cache/broker (not chosen).
- A numeric millisecond p95 SLO (not given). Latency is specified as **zero store/network on authorize**, not as a p95 number.
- **Gherkin** `.feature` files and a second BDD runner (Behave, Cucumber, pytest-bdd). Section 8 already is Given / When / Then; duplicating it would split the source of truth.

### 1.3 Definitions

| Term | Meaning |
| --- | --- |
| Hybrid RBAC | One role per user (`user` or `admin`) **and** permissions from two grant tables: role→permission and user→permission. Effective rights = union of both. Extra user grants do not invent a third role. |
| Access token | HS256 JWT issued at login; claims include `role` and the effective `permissions` snapshot |
| Authorize path | Handling of a request that already carries a Bearer token |
| Login path | `POST /auth/login` |
| Role grant | Permission attached to a role (every user with that role inherits it) |
| Extra user grant | Permission attached directly to a user (exception overlay) |
| Effective permissions | Role grants ∪ extra user grants |
| Init CLI | Terminal command that creates schema, seeds roles **and the default permission catalog**, and inserts the first admin |
| Operator | Person who runs the init CLI on first setup (may be the same person as Administrator) |
| Default catalog | Permission names seeded at init and attached to `admin` / `user` (section 4) |
| Object-level 404 | Role `user` asking for another user’s `{id}` gets HTTP 404 (same as missing), never 403 |
| TDD | For each AC (or FR slice): write a failing pytest (`red`), implement the minimum to pass (`green`), then refactor. Oracles are section 8, not a second Gherkin tree. |

### 1.4 Assumptions

- Solo delivery, 60 h × 4 phases (see vision effort table).
- Shared secret HS256; `role` and effective `permissions` are in the token so authorize does not read the database.
- Permission or role-grant changes after issue are visible only after the user logs in again (token snapshot of hybrid RBAC).
- First-time bootstrap is a **terminal** init command, not an unauthenticated HTTP register endpoint.
- Construction follows **TDD** (`FR-31`): no production behavior for an AC until its pytest is red, then green. Gherkin/Behave/Cucumber files are **not** used (`FR-33`).

### 1.5 Authorization model: hybrid RBAC

This product is **hybrid RBAC**, not role-only RBAC and not a permission-only ACL.

| Piece | Rule |
| --- | --- |
| Role assignment | Every user has **exactly one** role: `user` or `admin` (`FR-17`). Extra permissions never add a third catalog name (`FR-14`). |
| Role grants | Permissions attached to a role apply to every user with that role (`FR-20`). |
| Extra user grants | Permissions attached directly to a user, on top of the role (`FR-19`). Optional (`0..*`). |
| Effective permissions | **Role grants ∪ extra user grants** (`FR-21`). Duplicates collapse (same permission name once in the token). |
| Token snapshot | Login copies `role` and the effective permission names into the JWT. Authorize reads **only** those claims (`FR-11`). |
| **Default catalog** | Seeded at init (`FR-13`, `FR-26`). `admin` gets all-users CRUD. `user` gets self CRUD only. Extra grants may add permissions but never a third role. |
| What this closes | Open-ended role catalogs; “permissions without a role”; treating extra grants as a new role. |

---

## 2. Actors and journeys

Aligned with **VC-001**.

![Initialize — first-time project setup](docs/diagrams/seq-init.png)

Source: [Lucidchart — Initialize](https://lucid.app/lucidchart/a46d483a-59a2-4253-b960-03d78d24acb5/edit)

![Login — issue JWT (role in claims)](docs/diagrams/seq-login.png)

Source: [Lucidchart — Login](https://lucid.app/lucidchart/87ba0496-0121-4f25-98ee-4aeed23be2c3/edit)

![Authorize — local JWT verify (hot path, no DB)](docs/diagrams/seq-authorize.png)

Source: [Lucidchart — Authorize](https://lucid.app/lucidchart/d14b5a42-15d0-42b1-945c-421a5acf8406/edit)

| Actor | Journeys |
| --- | --- |
| Operator | Runs the init CLI on an empty (or not-yet-bootstrapped) store. Does not need the HTTP API to be serving. |
| End user | Register is **admin-provisioned** in v0.1. Login (receives `user_id`); CRUD **own** profile (`/users/me` or `/users/{sub}`); cannot request other users. |
| Administrator | Login; CRUD **all** users; assign `user` or `admin`; list roles; grant permissions to a role or extra permissions to a user (hybrid RBAC). |
| Peer application | Does not call this service on its hot path. Verifies JWT with the same secret; optionally calls login/admin APIs over HTTPS. |

**J-0 Initialize.** Operator runs a terminal command. The script reads `DATABASE_URL` (default `sqlite:///./rbac.db` if unset; otherwise the operator’s SQLite path or server URL), `JWT_SECRET`, and `ADMIN_*`. It creates the schema, seeds roles `user` and `admin`, seeds the **default permission catalog** (section 4), and inserts the first admin if none exists.

**J-1 Login.** Client submits username and password → identity store read (user + role) → password hash verify → JWT + `user_id` → 200.

**J-2 Authorize.** Client sends Bearer JWT → signature + expiry check in process → permission / ownership check → 200, 401, 403, or 404. **No SQL for the identity decision.** Object-level denials for *other* users return **404** (no existence leak).

**J-3 Admin user.** Administrator with role `admin` CRUD any user (`users:create|read|update|delete` on all rows).

**J-4 Hybrid grants.** Administrator attaches permissions to a role (defaults) and/or extra permissions to a user (exceptions). The next login copies the union into the token.

**J-5 Self profile.** A caller with role `user` reads/updates/deletes **only** the row whose `id` equals token `sub` (also `GET /users/me`). Requests for any other `id` return 404. They cannot create users or list `/users`.

---

## 3. Functional requirements

### 3.1 Authentication and tokens

| ID | Requirement | Vision |
| --- | --- | --- |
| FR-01 | The service SHALL expose `POST /auth/login` accepting JSON `{ "username": string, "password": string }`. | O4, VF-001 |
| FR-02 | On valid credentials, the service SHALL return HTTP 200 and JSON `{ "access_token": string, "token_type": "bearer", "user_id": number }`. `user_id` SHALL equal the persisted User.id and the JWT `sub` (recoverable after login without decoding the token). | O4 |
| FR-03 | On unknown user or wrong password, the service SHALL return HTTP 401 with the **same** public body (no distinct “unknown user” vs “bad password”). | O4 |
| FR-04 | The access token SHALL be a JWT signed with HS256 using `JWT_SECRET`. | Tech constraint |
| FR-05 | Token payload SHALL include at least `sub` (user id), `role` (`user` or `admin`), `permissions` (array of permission name strings), `exp`, and `iat`. | O1, O3 |
| FR-06 | Passwords SHALL be stored only as a one-way hash. The API SHALL never return a password or hash. | Business constraint |
| FR-07 | Login SHALL load the user and their role in **one** credential read (single query or equivalent join), then verify the hash in process. | O4 |

### 3.2 Authorization

| ID | Requirement | Vision |
| --- | --- | --- |
| FR-08 | Protected routes SHALL obtain the caller from `Authorization: Bearer <jwt>` via in-process verify (signature, `exp`). | O1, VF-001 |
| FR-09 | Missing, malformed, expired, or invalid-signature tokens SHALL yield HTTP 401. | O1 |
| FR-10 | A valid token that lacks the **permission** required for the operation SHALL yield HTTP **403** when the operation is not tied to another user’s id (e.g. list all users, create a user, list roles). | O2 |
| FR-10a | A valid token that targets **another** user’s id (GET/PATCH/DELETE `/users/{id}` where `{id}` ≠ token `sub`) SHALL yield HTTP **404**, not 403, so the response does not disclose whether that id exists. | O2, NFR-09 |
| FR-11 | The authorize path SHALL NOT query the identity store (0 round trips). Role, permissions, and `sub` used for the decision SHALL come from the token. Loading the user **row** after a successful allow is not an authorize hop. | O1 |
| FR-12 | Peer applications SHALL be able to repeat FR-08–FR-11 using the same `JWT_SECRET` without calling this service. | O3 |

### 3.3 Users, roles, and hybrid RBAC grants

| ID | Requirement | Vision |
| --- | --- | --- |
| FR-13 | At startup or migration, the service SHALL seed roles named exactly `user` and `admin`. | O2, VD-001 |
| FR-14 | The service SHALL reject assigning any role name other than `user` or `admin`. | O2 |
| FR-15 | An administrator SHALL be able to **create, read, update, and delete any user** (all rows). | O2, default catalog |
| FR-15a | A caller with role `user` SHALL be able to **read, update, and delete only their own row** (`id` = token `sub`). They SHALL NOT create users or read/update/delete other rows. | O2, default catalog |
| FR-15b | A caller with role `user` SHALL NOT change their own `role` (no self-promotion to `admin`). | O2 |
| FR-16 | Username and email SHALL be unique. | VD-001 |
| FR-17 | Every user SHALL have exactly one role (`role_id` required). | VD-001 |
| FR-18 | Admin SHALL be able to list all users and list roles. Role `user` SHALL NOT list all users. | O2 |
| FR-19 | Admin MAY attach extra permissions to a user (**hybrid** overlay). Duplicate `(user_id, permission_id)` is forbidden. Extra grants SHALL NOT change the user’s role name. | VD-001 |
| FR-20 | Admin MAY attach permissions to a role (defaults for that role). Duplicate `(role_id, permission_id)` is forbidden. | VD-001 |
| FR-21 | Effective permissions at login SHALL be the **hybrid** union of the user’s role permissions and extra user permissions, and SHALL be copied into the token (`FR-05`). | VD-001, O1 |
| FR-21a | Init SHALL seed the **default permission catalog** (section 4) and attach those permissions to roles `admin` and `user`. | O2, FR-26 |

### 3.4 First-time initialization

| ID | Requirement | Vision |
| --- | --- | --- |
| FR-24 | The product SHALL provide a **terminal** init command (`python -m app.cli init` and/or `scripts/init.sh`) that does **not** require the HTTP API to be running. | R6, VF-001, VA-001 |
| FR-25 | Init SHALL use `DATABASE_URL` from the environment. If unset, it SHALL default to `sqlite:///./rbac.db`. If the operator changed the store (other SQLite path, PostgreSQL, or MySQL), they SHALL pass that URL; init SHALL NOT silently ignore a provided URL. | VA-001, NFR-03 |
| FR-26 | Init SHALL connect with that URL, create or migrate the schema, seed roles named exactly `user` and `admin` (same as FR-13), and seed the default permission catalog plus role grants (`FR-21a`). | O2, VD-001 |
| FR-27 | Init SHALL require `ADMIN_USERNAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` when no administrator exists, hash the password (FR-06), and insert a user with role `admin`. | R6, O2 |
| FR-28 | If an administrator already exists, init SHALL skip creating another admin (idempotent bootstrap) and SHALL NOT overwrite the existing password. | R6 |
| FR-29 | Init SHALL fail closed (non-zero exit) if `JWT_SECRET` is missing, if the database cannot be reached, or if `ADMIN_*` is missing when a first admin must be created. | NFR-05, R6 |
| FR-30 | Init SHALL print the resolved store URL (without secrets) and a success or error summary. | VA-001 |

### 3.5 Operations

| ID | Requirement | Vision |
| --- | --- | --- |
| FR-22 | `GET /health` SHALL return HTTP 200 without requiring a token (liveness of the process). | VA-001 |
| FR-23 | Settings SHALL be read from the environment: `JWT_SECRET` (required at runtime), `JWT_ALGORITHM` (default HS256), `ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_URL` (default SQLite file). Init additionally reads `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`. | VA-001 |

### 3.6 Development process (TDD)

TDD is a **required step of Construction**, not an optional Testing-phase add-on. See [Test-strategy.md](Test-strategy.md) §2.0.

| ID | Requirement | Vision |
| --- | --- | --- |
| FR-31 | Construction SHALL implement each acceptance criterion with **TDD**: (1) add or extend a pytest that encodes the AC and **fails**; (2) write the minimum production code to make it **pass**; (3) **refactor** with the suite still green. Production behavior for that AC SHALL NOT land without a prior red test. | Test strategy, Construction |
| FR-32 | Each AC in section 8 SHALL map to one or more pytest functions named from the AC id (e.g. `test_ac_fr_10a_…`). pytest is the executable form of Given / When / Then. | Test strategy OBJ-3 |
| FR-33 | The cycle SHALL NOT add Gherkin `.feature` files or a second runner (Behave, Cucumber, pytest-bdd). Those would duplicate section 8. | Test strategy 2.7 |
| FR-34 | The pytest suite SHALL run as regression after every subsequent change (confirmation of the failing AC plus the full suite). | Test strategy 2.6 |

---

## 4. Default permissions and HTTP matrix

Seeded at init (`FR-21a`). Codes are stable `Permission.name` values. Effective rights at login = these role grants ∪ any extra user grants (`FR-21`). Extra grants do **not** add a third role.

### 4.1 Default permission catalog

| Permission | Meaning | Granted to `admin` | Granted to `user` |
| --- | --- | --- | --- |
| `users:create` | Create a new user | yes | no |
| `users:read` | Read **any** user row; list all users | yes | no |
| `users:update` | Update **any** user row (including role) | yes | no |
| `users:delete` | Delete **any** user row | yes | no |
| `users:read_self` | Read own row (`id` = token `sub`) | yes | yes |
| `users:update_self` | Update own row (not `role`) | yes | yes |
| `users:delete_self` | Delete own row | yes | yes |
| `roles:read` | List the role catalog | yes | no |
| `roles:grant` | Attach a permission to a role | yes | no |
| `users:grant` | Attach an extra permission to a user | yes | no |

**Net effect**

- **`admin`:** CRUD on **all** users in the store, plus role/grant administration.
- **`user`:** CRUD on **own** information only. Cannot list users, cannot GET/PATCH/DELETE another `{id}`, cannot create users.

`GET /users/me` is an alias for `GET /users/{token.sub}`. After login, `user_id` is in the 200 body **and** in JWT `sub` (`FR-02`, `FR-05`).

### 4.2 HTTP responses (no information leak)

Public error bodies SHALL NOT name usernames, emails, whether an id exists, or which credential field failed. Prefer a short `detail` string equal for all cases of the same status.

| Status | When | Public body (illustrative) |
| --- | --- | --- |
| 200 / 201 | Allowed and the resource is returned or created | Success payload; never hashes |
| 401 | Missing, malformed, expired, or invalid token; or login failed | `{ "detail": "Unauthorized" }` |
| 403 | Authenticated, but the **operation** is not allowed (list-all, create, roles, grants) | `{ "detail": "Forbidden" }` |
| 404 | Authenticated `user` targets **another** `{id}`; or admin targets a truly missing `{id}` | `{ "detail": "Not found" }` |
| 409 | Unique username/email conflict on a write the caller is allowed to attempt | `{ "detail": "Conflict" }` |
| 422 | Invalid body | FastAPI validation |

A `user` MUST receive **404** (not 403) for `GET`/`PATCH`/`DELETE /users/{id}` when `{id}` ≠ `sub`, whether or not that row exists. That avoids filtering/leaking existence of other accounts.

### 4.3 Operation matrix

Unauthenticated = no valid Bearer token.

| Operation | Unauthenticated | `user` | `admin` |
| --- | --- | --- | --- |
| `POST /auth/login` | Allow (200 or 401) | Allow | Allow |
| `GET /health` | Allow | Allow | Allow |
| `GET /users/me` | 401 | Allow (own row) | Allow (own row) |
| `GET /users` | 401 | 403 | Allow |
| `POST /users` | 401 | 403 | Allow (201) |
| `GET /users/{id}` | 401 | Allow if `{id}`=`sub`; else **404** | Allow if exists; else 404 |
| `PATCH /users/{id}` | 401 | Allow if `{id}`=`sub` (not `role`); else **404** | Allow if exists; else 404 |
| `DELETE /users/{id}` | 401 | Allow if `{id}`=`sub`; else **404** | Allow if exists; else 404 |
| `GET /roles` | 401 | 403 | Allow |
| `POST /roles/{id}/permissions` (if exposed) | 401 | 403 | Allow |
| `POST /users/{id}/permissions` (if exposed) | 401 | 403 | Allow |

Peer applications apply the same 401/403/404 rules locally using token claims (`FR-12`). Ownership (`sub` vs `{id}`) is decided from the token; it does not require a store hop.

---

## 5. Data requirements (hybrid RBAC)

Aligned with **VD-001** and the [User RBAC](https://lucid.app/lucidchart/630829d8-5ce5-4bb5-b3f2-fffba2934f9d/edit) logical model. The schema is hybrid: `User.role_id` is the RBAC assignment; `roles_permissions` and `users_permissions` are the two grant sources.

| Entity | Required fields | Rules |
| --- | --- | --- |
| User | id, username (unique), email (unique), hashed_password, role_id (FK, not null) | No string `role` column as source of truth |
| Role | id, name (unique, not null) | `name ∈ {user, admin}` |
| Permission | id, name (unique, not null) | Stable codes from the default catalog (section 4); extra codes allowed later |
| users_permissions | user_id, permission_id | Unique pair; each end 1 — 0..* |
| roles_permissions | role_id, permission_id | Unique pair; each end 1 — 0..* |

Cardinalities: User **\*** — **1** Role; User **1** — **0..\*** extra grants; Role **1** — **0..\*** role grants.

Init inserts the default catalog (section 4) as `Permission` rows and `roles_permissions` rows for `admin` and `user`. Extra `users_permissions` rows are empty until an administrator adds overlays.

This is **hybrid RBAC**: the role is mandatory and unique per user; permissions are optional on both the role and the user. A user with role `user` plus extra grants is still role `user` (not a new catalog name).

---

## 6. Non-functional requirements

Quality attributes are **not** technology constraints. See vision section “Business and technology constraints”.

| ID | Requirement | Notes |
| --- | --- | --- |
| NFR-01 | **Authorize latency (architectural SLO):** the authorize path SHALL perform 0 identity-store round trips and 0 extra network hops to this product. | O1; no millisecond p95 was specified |
| NFR-02 | **Login latency:** login MAY use the relational store; default SQLite is colocated (no DB network RTT). | O4, VA-001 |
| NFR-03 | **Portability:** changing `DATABASE_URL` to PostgreSQL or MySQL SHALL not require code changes beyond supported SQLAlchemy URLs and driver install. | Tech constraint |
| NFR-04 | **Scaling writes:** multiple concurrent writer processes SHALL use a server RDBMS, not shared-file SQLite. Authorize remains NFR-01 either way. | VA-001 |
| NFR-05 | **Confidentiality:** `JWT_SECRET` and `DATABASE_URL` SHALL NOT be in the container image or git. | R5 |
| NFR-06 | **Integrity of tokens:** HS256 verify MUST fail closed (invalid token → 401, never 200). | FR-09 |
| NFR-07 | **Stateless compute:** application processes SHALL NOT keep login session state in memory; the token is the session. | VA-001 |
| NFR-08 | **Health:** `GET /health` SHALL not depend on a successful DB ping for process liveness (optional readiness may check DB later; not required in v0.1). | FR-22 |
| NFR-09 | **No existence leak:** HTTP error responses SHALL NOT disclose whether a username, email, or user id exists except via a successful 200/201 the caller is allowed to receive. Cross-user object access by role `user` is 404 (`FR-10a`). Login failures are 401 (`FR-03`). | FR-03, FR-10a |

---

## 7. API sketch

Base URL: service origin. JSON UTF-8. Errors: `{ "detail": string }` unless FastAPI validation errors apply.

### 7.1 `POST /auth/login`

**Request**

```json
{ "username": "alice", "password": "secret" }
```

**Success (200)**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": 1
}
```

`user_id` is the persisted User.id. The JWT `sub` claim SHALL be that same value as a string or number (implementation MUST treat them as equal). Clients MAY use `user_id` without decoding the token.

**Errors:** `401` FR-03 (same body for unknown user and wrong password); `422` invalid body.

### 7.2 Authenticated requests

Header: `Authorization: Bearer <access_token>`

### 7.3 `GET /health`

**Responses:** `200` `{ "status": "ok" }` (or equivalent).

### 7.4 Users

Public user fields only (no password, no hash). `{id}` is the integer User.id.

| Method | Path | `user` | `admin` | Errors |
| --- | --- | --- | --- | --- |
| GET | `/users/me` | 200 own row | 200 own row | 401 |
| GET | `/users` | 403 | 200 list | 401, 403 |
| POST | `/users` | 403 | 201 created | 401, 403, 409, 422 |
| GET | `/users/{id}` | 200 if `{id}`=`sub`; else 404 | 200 or 404 | 401, 404 |
| PATCH | `/users/{id}` | 200 if `{id}`=`sub`; else 404. Body MUST NOT accept `role`. | 200 or 404; MAY set `role` | 401, 404, 409, 422 |
| DELETE | `/users/{id}` | 204 if `{id}`=`sub`; else 404 | 204 or 404 | 401, 404 |

**Create body (illustrative, admin only)**

```json
{
  "username": "bob",
  "email": "bob@example.com",
  "password": "secret",
  "role": "user"
}
```

`role` in the body is the catalog name `user` | `admin`, mapped to `role_id` internally.

### 7.5 Roles (admin)

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| GET | `/roles` | 200 `[{ "id", "name" }]` | 401, 403 |

Creating new role **names** is out of scope (FR-13, FR-14).

### 7.6 Init CLI (terminal)

Not an HTTP route. Example:

```bash
export JWT_SECRET="replace-me"
# omit DATABASE_URL to keep sqlite:///./rbac.db
# or set a modified SQLite path / Postgres / MySQL URL:
# export DATABASE_URL="sqlite:///./custom.db"
# export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/rbac"
export ADMIN_USERNAME="admin"
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="choose-a-strong-password"
python -m app.cli init
# equivalent: ./scripts/init.sh
```

**Exit:** `0` on success (including idempotent skip of an existing admin); non-zero on FR-29 failures.

---

## 8. Acceptance criteria

These rows **are** the BDD specification (Given / When / Then). Construction turns each row into pytest under TDD (`FR-31`, `FR-32`). Do not rewrite them as `.feature` files.

| ID | Given / When / Then |
| --- | --- |
| AC-FR-01 | Given a seeded `user` account, when `POST /auth/login` is called with the correct password, then the response is 200, JSON includes `user_id` equal to that account’s id, and `access_token` is a JWT whose `sub` equals `user_id` and whose `role` is `user`. |
| AC-FR-03 | Given a wrong password **or** an unknown username, when login is called, then the response is 401 and both cases share the same public `detail`. |
| AC-FR-07 | Given login succeeds, when store query count for that request is measured, then there is exactly one credential read for user+role (no per-permission N+1 on that path beyond what is required to assemble FR-21 in that same read/join). |
| AC-FR-09 | Given no `Authorization` header, when `GET /users` is called, then the response is 401. |
| AC-FR-10 | Given a valid token with `role=user`, when `GET /users` is called, then the response is 403. |
| AC-FR-10a | Given a valid token with `role=user` and `sub=A`, when `GET /users/B` is called (B ≠ A), then the response is **404** with the same body whether B exists or not. |
| AC-FR-10b | Given a valid token with `role=user` and `sub=A`, when `GET /users/A` or `GET /users/me` is called, then the response is 200 and the body is A’s public fields. |
| AC-FR-10c | Given a valid token with `role=user` and `sub=A`, when `PATCH /users/A` sets `email`, then the response is 200; when the body includes `"role": "admin"`, then the response is 422 or the `role` field is ignored and the stored role remains `user`. |
| AC-FR-10d | Given a valid admin token, when `GET /users` then `PATCH /users/{id}` then `DELETE /users/{id}` are called for another user, then those succeed (200/204) subject to uniqueness rules. |
| AC-FR-11 | Given a valid admin token, when `GET /users` is called, then the handler does not open a DB session for **authorization** (DB may be used afterwards to list users). |
| AC-FR-14 | Given an admin, when create user is called with `"role": "superadmin"`, then the response is 422 or 400 and no row is inserted. |
| AC-FR-16 | Given an existing username, when create user reuses it, then the response is 409. |
| AC-FR-21 | Given role `user` with permission `items:read` and an extra user grant `items:write`, when that user logs in, then the token `role` is `user` and `permissions` contains both names (union, no third role). |
| AC-FR-21a | Given a fresh init, when the permission catalog is listed, then `admin` has `users:create`, `users:read`, `users:update`, `users:delete` (and self variants), and `user` has only `users:read_self`, `users:update_self`, `users:delete_self`. |
| AC-FR-24 | Given an empty store and valid `ADMIN_*` plus `JWT_SECRET`, when `python -m app.cli init` is run, then roles `user` and `admin` exist, the default catalog is granted, and one user with role `admin` can `POST /auth/login`. |
| AC-FR-25 | Given `DATABASE_URL=sqlite:///./custom.db`, when init is run, then the schema is created at that path (not at the default `./rbac.db`). |
| AC-FR-28 | Given an admin already exists, when init is run again, then exit is 0 and the existing admin password is unchanged. |
| AC-FR-29 | Given `JWT_SECRET` is unset, when init is run, then the process exits non-zero and no admin is inserted. |
| AC-NFR-03 | Given the app started with SQLite, when `DATABASE_URL` is pointed at an empty PostgreSQL database and migrations are applied, then login still succeeds for a seeded user. |
| AC-NFR-05 | Given the built image, when the filesystem is scanned, then `JWT_SECRET` is not present as a default baked file. |
| AC-FR-31 | Given an AC in section 8 with no production code yet, when Construction starts that slice, then a pytest named from that AC id exists and fails before the implementation is added; after implementation the same test passes. |
| AC-FR-33 | Given the repository, when `*.feature` and Behave/Cucumber/pytest-bdd configs are listed, then none are required or present for v0.1. |

---

## 9. Traceability

| Spec ID | Vision / view | Lucid |
| --- | --- | --- |
| FR-01–FR-07, AC-FR-01, AC-FR-07 | O4, VF-001 identity + token issue | [Login sequence](https://lucid.app/lucidchart/87ba0496-0121-4f25-98ee-4aeed23be2c3/edit) |
| FR-08–FR-12, FR-10a, NFR-01, NFR-09 | O1, O3, VF-001 token verify | [Authorize sequence](https://lucid.app/lucidchart/d14b5a42-15d0-42b1-945c-421a5acf8406/edit) |
| FR-13–FR-21a, AC-FR-10–AC-FR-10d, AC-FR-21 | O2, VD-001 hybrid RBAC, default catalog | [User RBAC data model](https://lucid.app/lucidchart/630829d8-5ce5-4bb5-b3f2-fffba2934f9d/edit) |
| FR-24–FR-30, AC-FR-24–AC-FR-29, J-0 | R6, VF-001 Init CLI, VA-001 | [Initialize sequence](https://lucid.app/lucidchart/a46d483a-59a2-4253-b960-03d78d24acb5/edit) |
| Actors, J-0–J-5 | VC-001 | [Architecture p.1 context](https://lucid.app/lucidchart/ce9220eb-71a9-462a-b15e-343d00728c1f/edit) |
| HTTP API, token, admin, adapter, Init CLI | VF-001 UML components | [UML containers](https://lucid.app/lucidchart/b7de0d28-4aff-4a3a-9d0b-d67e8c5bc42f/edit), [UML building blocks](https://lucid.app/lucidchart/d9604080-5380-4a18-8964-eea7faf66d35/edit) |
| FR-22–FR-23, NFR-02–NFR-08 | VA-001 UML deployment | [UML deployment](https://lucid.app/lucidchart/2919245a-bdd6-4ee7-a45f-29d8c6008bab/edit) |
| FR-31–FR-34, AC-FR-31, AC-FR-33 | Construction TDD; no Gherkin | [Test-strategy.md](Test-strategy.md) |

---

## 10. Open points (non-blocking for v0.1)

- Public self-registration vs admin-only provisioning (this spec: **admin-only**).
- Numeric p95 latency target (not specified; NFR-01 is architectural).
- Token TTL default (`ACCESS_TOKEN_EXPIRE_MINUTES`); recommend 15–60 minutes until a product owner sets it.
- Whether `GET /health` later gains a separate readiness probe that checks the database.
- Whether a `user` deleting self (`users:delete_self`) remains in v0.1 or is deferred (this spec: **allowed**).
