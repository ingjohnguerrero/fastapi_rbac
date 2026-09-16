<!--
Sync Impact Report
- Version change: (template placeholders) → 1.0.0 (initial ratification)
- Modified principles: [PRINCIPLE_1_NAME] → I. Token-First Authorize;
  [PRINCIPLE_2_NAME] → II. Hybrid RBAC;
  [PRINCIPLE_3_NAME] → III. Test-First (NON-NEGOTIABLE);
  [PRINCIPLE_4_NAME] → IV. Contract and Integration Tests;
  [PRINCIPLE_5_NAME] → V. Simplicity
- Added sections: Security and Runtime Constraints; Development Workflow
- Removed sections: none (template slots filled)
- Templates:
  - .specify/templates/plan-template.md ✅ updated (Constitution Check gates)
  - .specify/templates/spec-template.md ✅ updated (constitution constraints, GWT/TDD)
  - .specify/templates/tasks-template.md ✅ updated (TDD mandatory; app/ layout)
  - .specify/templates/commands/*.md ⚠ none present (git extension commands only; no agent-specific names)
  - README.md ✅ updated (constitution link)
- Follow-up TODOs: none deferred
-->

# fastapi_rbac Constitution

## Core Principles

### I. Token-First Authorize
Authorize MUST decide allow or deny from the signed JWT only. Claims MUST
include `sub` (user id), `role` (`user` or `admin`), `permissions`, `exp`,
and `iat`. The authorize path MUST perform **0** identity-store round trips
and **0** extra network hops to this product. Loading a user row **after**
an allow is not an authorize hop. Peer applications MUST be able to repeat
the same decision with `JWT_SECRET` and MUST NOT call this service on their
hot path.

**Rationale**: Stakeholder objective O1 and NFR-01. A store lookup on every
request reintroduces latency and coupling (risk R1).

### II. Hybrid RBAC
Every user MUST have **exactly one** role: `user` or `admin`. The catalog
MUST reject any other role name. Permissions come from role grants and
optional extra user grants. Effective rights MUST be the union of both,
copied into the token at login. Extra grants MUST NOT create a third role.
Default catalog: `admin` CRUD **all** users; `user` CRUD **own** row only
(`id` = token `sub`).

**Rationale**: O2 and Requirements FR-13–FR-21a. Role-only RBAC or a
permission-only ACL would break the stated model.

### III. Test-First (NON-NEGOTIABLE)
Construction MUST use TDD for every acceptance criterion (AC): (1) add a
pytest named from the AC id that **fails**, (2) write the minimum
production code to make it **pass**, (3) refactor with the suite still
green. Production behavior for an AC MUST NOT land without a prior red
test. pytest MUST be the executable Given / When / Then. Gherkin
`.feature` files and a second runner (Behave, Cucumber, pytest-bdd)
MUST NOT be added.

**Rationale**: FR-31–FR-34. Section 8 of Requirements.md is already GWT;
a second spec language splits the source of truth.

### IV. Contract and Integration Tests
The HTTP operation matrix MUST be automated (401 / 403 / 404 / 409 / 422)
with identical public `detail` per status. Init CLI MUST be tested against
`DATABASE_URL` (default SQLite path honoured; fail-closed without
`JWT_SECRET`). Login MUST be measurable as **one** credential read.
Authorize tests MUST fail if a DB session is opened for the **decision**.
A peer verifier module MUST accept a valid token with **zero** HTTP calls
to this app.

**Rationale**: Test-strategy experiments PR-01, PS-01–PS-03, PI-01–PI-02
and AC-FR-* / AC-NFR-*.

### V. Simplicity
The product MUST remain a single FastAPI process plus a terminal Init CLI.
MUST NOT add an API gateway, cache, broker, corporate IdP, or OAuth2/OIDC
server unless this constitution is amended. Default store is SQLite;
`DATABASE_URL` MUST be honoured when set. First-time bootstrap MUST be
the Init CLI, not an unauthenticated HTTP register.

**Rationale**: Technology constraints already chose FastAPI, HS256, and a
relational store. Extra moving parts would violate YAGNI and NFR-01.

## Security and Runtime Constraints

- `JWT_SECRET` MUST be required at runtime and at init. Init MUST exit
  non-zero if it is missing. The secret MUST NOT be committed or baked
  into the container image.
- Passwords MUST be stored as a one-way hash and MUST NEVER appear in API
  responses.
- Unauthenticated or invalid tokens MUST yield HTTP **401**. Disallowed
  operations (list-all, create, roles) MUST yield **403**. Role `user`
  targeting another `{id}` MUST yield **404** with the same body whether
  that id exists or not. Login MUST use one **401** body for unknown user
  and wrong password.
- `GET /health` MUST NOT require a successful database ping.
- Settings MUST come from the environment (`JWT_SECRET`, `JWT_ALGORITHM`
  default HS256, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_URL`, `ADMIN_*`
  at init).

## Development Workflow

- **Analysis**: freeze AC as Given / When / Then in Requirements.md.
- **Construction**: TDD per AC (`test_ac_fr_*` / `test_ac_nfr_*`); package
  layout is `app/` (`python -m app.cli init`, `uvicorn app.main:app`).
- **Testing**: re-run the suite, close HTTP matrix gaps, run architecture
  experiments (0 hops, leak 404, image scan, optional Postgres).
- The pytest suite MUST run as regression after every subsequent change.
- Feature specs and plans MUST pass the Constitution Check in
  `plan.md` before implementation tasks start.
- Runtime guidance: [Requirements.md](../../Requirements.md),
  [Architecture-vision.md](../../Architecture-vision.md),
  [Test-strategy.md](../../Test-strategy.md), [README.md](../../README.md).

## Governance

This constitution supersedes conflicting practice in specs, plans, and
ad-hoc code. Amendments MUST update this file, bump the version, and
propagate to `.specify/templates/` plus README if principles change.

Versioning:

- **MAJOR**: remove or redefine a principle (incompatible governance).
- **MINOR**: add a principle or materially expand a section.
- **PATCH**: clarifications, wording, non-semantic refinements.

Reviews and `/speckit-plan` MUST verify the Constitution Check gates.
Unjustified complexity (new services, extra stores, Gherkin, store hops
on authorize) MUST be recorded in the plan Complexity Tracking table or
the work MUST NOT proceed.

**Version**: 1.0.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-16
