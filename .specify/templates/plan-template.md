# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12+

**Primary Dependencies**: FastAPI, uvicorn, SQLAlchemy, PyJWT (HS256)

**Storage**: SQLite default (`sqlite:///./rbac.db`); PostgreSQL/MySQL via `DATABASE_URL`

**Testing**: pytest, FastAPI TestClient, coverage.py (branch); TDD required

**Target Platform**: HTTP JSON service (uvicorn); terminal Init CLI

**Project Type**: web-service + CLI bootstrap

**Performance Goals**: Authorize path = 0 identity-store round trips (not a millisecond p95)

**Constraints**: Hybrid RBAC (`user`|`admin`); secrets from env; deny 401/403/404 without existence leak; no Gherkin

**Scale/Scope**: Single process; SQLite colocated unless multiple writers (then server RDBMS)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Copy from `.specify/memory/constitution.md`. All items MUST be true or listed
in Complexity Tracking with justification.

- [ ] **I. Token-First Authorize**: allow/deny uses JWT claims only; 0 identity-store hops on the authorize path
- [ ] **II. Hybrid RBAC**: roles are only `user` and `admin`; extra grants do not add a third role
- [ ] **III. Test-First**: each AC has a failing pytest (`test_ac_*`) before production code; no Gherkin
- [ ] **IV. Contract tests**: HTTP matrix (401/403/404) and Init CLI / `DATABASE_URL` covered
- [ ] **V. Simplicity**: no new gateway, cache, broker, or IdP; SQLite default; Init CLI for bootstrap
- [ ] **Security**: `JWT_SECRET` from env; no hashes in responses; existence leak is 404 not 403
- [ ] **Layout**: production code under `app/`; tests under `tests/`

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── main.py              # FastAPI app
├── cli.py               # python -m app.cli init
├── api/
├── auth/                # JWT issue/verify (no store on authorize)
├── models/
└── adapters/            # SQLAlchemy / DATABASE_URL

tests/
├── unit/                # hybrid union, token verify, query-counter
├── integration/         # TestClient HTTP matrix, Init CLI
└── contract/            # peer JWT verify (0 HTTP)
```

**Structure Decision**: Single FastAPI package `app/` plus `tests/` (constitution V. Simplicity). Do not introduce frontend, mobile, or extra services without a constitution amendment.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
