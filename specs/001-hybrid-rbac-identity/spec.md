# Feature Specification: Hybrid RBAC identity

**Feature Branch**: `001-hybrid-rbac-identity`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: product requirements in [Requirements.md](../../Requirements.md) (identity and access: sign-in, two roles, self vs all-people management, signed proof for peers, first-time setup, denials that do not leak other accounts).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-time setup (Priority: P1)

An operator stands up an empty identity store for the first time. They supply connection details (or keep the default local store), a signing secret, and the first administrator’s username, email, and password. Setup creates the two roles, the default permission catalog, and that first administrator. It does not require the online service to be running. If an administrator already exists, running setup again does not create a second admin or overwrite the existing password.

**Why this priority**: Without a first administrator, nobody can sign in or provision people. This is the bootstrap for every other story.

**Independent Test**: On an empty store, run setup with valid admin credentials and secret; one administrator can sign in. Run setup again; the existing password is unchanged. Run setup without a signing secret; it fails and no admin is created.

**Acceptance Scenarios**:

1. **Given** an empty identity store and a signing secret plus first-admin credentials, **When** the operator runs first-time setup, **Then** roles `user` and `admin` exist, the default permission catalog is granted, and that administrator can sign in.
2. **Given** a custom store location, **When** setup runs, **Then** data is created at that location and not at the default location.
3. **Given** an administrator already exists, **When** setup runs again, **Then** it succeeds without changing the existing password.
4. **Given** the signing secret is missing, **When** setup runs, **Then** it fails and no administrator is inserted.

---

### User Story 2 - Sign in and recover identity (Priority: P1)

A provisioned person (ordinary member or administrator) signs in with username and password. On success they receive a signed access proof and their own identity number. The identity number on the proof matches the number returned in the successful response, so they can recover it without guessing. Wrong password and unknown username fail the same way in public.

**Why this priority**: Every later action depends on a successful sign-in. Identity recovery is required so a member can act on their own record.

**Independent Test**: Seed one member; sign in with the correct password and confirm identity number plus role. Sign in with a wrong password and with an unknown username; both fail identically in public.

**Acceptance Scenarios**:

1. **Given** a seeded member with role `user`, **When** they sign in with the correct password, **Then** they receive a signed access proof whose subject is their identity number and whose role is `user`, and the success response includes that same identity number.
2. **Given** a wrong password **or** an unknown username, **When** sign-in is attempted, **Then** both cases fail with the same public message and do not say which field was wrong.
3. **Given** a successful sign-in, **When** the identity directory reads for that attempt are counted, **Then** there is exactly one credential read for the person and their role (plus whatever is needed to assemble effective permissions in that same read).

---

### User Story 3 - Later access from the signed proof (Priority: P1)

After sign-in, the person (or another application that shares the signing secret) presents the access proof on later requests. Allow or deny is decided from that proof alone: who they are, their role, and their permissions. The identity directory is not consulted for that decision. Missing, expired, or forged proofs are refused. A peer application can make the same decision without calling this product.

**Why this priority**: The product’s reason to exist is a shared, low-latency proof. If every request looks up identity again, the product has failed.

**Independent Test**: Present a valid proof, a missing proof, and a tampered proof on a protected action. Confirm allow/deny without a directory lookup for the decision. Verify a standalone checker with only the shared secret accepts a valid proof and rejects a tampered one, with no call to this product.

**Acceptance Scenarios**:

1. **Given** no access proof, **When** a protected action is requested, **Then** the caller is refused as unauthenticated.
2. **Given** a valid proof whose role is not allowed to list all people, **When** they request the full people list, **Then** they are refused as forbidden (the operation is not allowed).
3. **Given** a valid administrator proof, **When** they request a protected action, **Then** the allow/deny decision does not open the identity directory (the directory may be used afterwards to load rows).
4. **Given** a valid proof and the shared signing secret, **When** a peer checks the proof locally, **Then** it can allow or deny with zero calls back to this product.

---

### User Story 4 - Administrator manages all people (Priority: P2)

An administrator creates, lists, updates, and removes any person. They assign only `user` or `admin`. Usernames and emails are unique. They can list the two-role catalog. They cannot invent a third role name.

**Why this priority**: Ordinary members are admin-provisioned in this version. Administration is the only way to add people after setup.

**Independent Test**: Sign in as administrator; create a person; list people; change them; remove them. Attempt a third role name; nothing is created. Reuse an existing username; conflict is reported.

**Acceptance Scenarios**:

1. **Given** a valid administrator proof, **When** they create, list, update, and remove another person, **Then** those actions succeed (subject to uniqueness).
2. **Given** an administrator, **When** they create a person with a role other than `user` or `admin`, **Then** the request is rejected and no person is stored.
3. **Given** an existing username, **When** create reuses it, **Then** the request conflicts and no duplicate is stored.
4. **Given** an ordinary member proof, **When** they try to list all people or create a person, **Then** they are refused as forbidden.

---

### User Story 5 - Member manages only themselves (Priority: P2)

An ordinary member reads, updates, and may remove **only** their own record. They cannot request another person’s information. Asking for someone else looks the same as asking for a person who does not exist. They cannot promote themselves to administrator.

**Why this priority**: Default permissions: members own their data; they must not discover other accounts.

**Independent Test**: Sign in as member A. Read and update A. Request B whether or not B exists; both look like “not found.” Attempt to set A’s role to `admin`; the stored role stays `user`.

**Acceptance Scenarios**:

1. **Given** a valid member proof for person A, **When** they request their own record (by “me” or by their identity number), **Then** they receive A’s public fields (never a password or hash).
2. **Given** a valid member proof for A, **When** they request person B (B ≠ A), **Then** the response is “not found” with the same public body whether B exists or not.
3. **Given** a valid member proof for A, **When** they update their email, **Then** the change is stored; **When** they try to set role to `admin`, **Then** the stored role remains `user`.
4. **Given** a valid member proof for A, **When** they request the full people list, **Then** they are refused as forbidden.

---

### User Story 6 - Extra permissions without a new role (Priority: P3)

An administrator may attach extra permissions to one person on top of that person’s role, and may attach permissions to a role for everyone with that role. The person’s role name does not change. The next sign-in carries the union of role permissions and extra permissions.

**Why this priority**: This is the hybrid overlay. Login and admin CRUD still work without it; it is the exception path.

**Independent Test**: Give role `user` a permission and the same person an extra permission. After they sign in, the proof still says role `user` and lists both permission names. Duplicate grants are rejected.

**Acceptance Scenarios**:

1. **Given** role `user` with permission `items:read` and an extra person grant `items:write`, **When** that person signs in, **Then** the proof role is `user` and permissions contain both names (union, no third role).
2. **Given** a fresh setup, **When** the default catalog is inspected, **Then** `admin` can create/read/update/delete all people (and self), and `user` has only self read/update/delete.
3. **Given** an extra grant already attached to a person, **When** the same grant is attached again, **Then** it is rejected as a duplicate.

---

### User Story 7 - Service liveness (Priority: P3)

Operators can ask whether the process is alive without signing in. That check does not depend on the identity store being reachable.

**Why this priority**: Needed to run and operate the service; not a user-facing journey.

**Independent Test**: Call liveness without credentials; it succeeds even if the store is down.

**Acceptance Scenarios**:

1. **Given** the process is running, **When** anyone requests liveness, **Then** they receive success without an access proof.

---

### Edge Cases

- Sign-in with empty or malformed body is rejected as invalid input, distinct from unauthenticated.
- Expired or malformed access proofs are refused as unauthenticated, never as success.
- A member deleting themselves is allowed in this version; after that, their proof must not grant further access to a missing record (treat as not found).
- Changing grants after a proof is issued is visible only after the next successful sign-in (proof is a snapshot).
- Setup without first-admin credentials on an empty store fails; nothing half-created should allow sign-in as admin.
- Unique email conflict on an allowed write is reported as conflict, not as “not found.”

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A person MUST be able to sign in with username and password.
- **FR-002**: On success the system MUST return a signed access proof and the person’s identity number; the number on the proof MUST match the number in the success response.
- **FR-003**: Unknown username and wrong password MUST fail the same way in public.
- **FR-004**: Passwords MUST be stored only as a one-way hash and MUST NEVER be returned.
- **FR-005**: Sign-in MUST load the person and their role in one credential read, then verify the secret in process.
- **FR-006**: Protected actions MUST identify the caller from the presented access proof (signature and expiry).
- **FR-007**: Missing, malformed, expired, or forged proofs MUST be refused as unauthenticated.
- **FR-008**: A valid proof that lacks permission for an operation not tied to another person’s id (list all, create, list roles) MUST be refused as forbidden.
- **FR-009**: A valid member proof that targets another person’s id MUST be refused as not found, whether or not that person exists.
- **FR-010**: Allow/deny MUST NOT consult the identity directory; role, permissions, and identity number MUST come from the proof.
- **FR-011**: Another application that shares the signing secret MUST be able to repeat FR-006–FR-010 without calling this product.
- **FR-012**: The catalog MUST contain exactly the roles `user` and `admin`; any other role name MUST be rejected.
- **FR-013**: Every person MUST have exactly one of those roles.
- **FR-014**: An administrator MUST be able to create, read, update, and delete any person.
- **FR-015**: An ordinary member MUST be able to read, update, and delete only their own record; they MUST NOT create people or access others.
- **FR-016**: An ordinary member MUST NOT change their own role.
- **FR-017**: Username and email MUST be unique.
- **FR-018**: Administrators MUST be able to list all people and list roles; ordinary members MUST NOT list all people.
- **FR-019**: Administrators MAY attach extra permissions to a person without changing that person’s role name; duplicate person–permission pairs MUST be rejected.
- **FR-020**: Administrators MAY attach permissions to a role; duplicate role–permission pairs MUST be rejected.
- **FR-021**: Effective permissions at sign-in MUST be the union of role permissions and extra person permissions, copied into the access proof.
- **FR-022**: First-time setup MUST seed the default permission catalog: `admin` all-people create/read/update/delete (and self); `user` self read/update/delete only; plus role listing and grant abilities for `admin` only.
- **FR-023**: First-time setup MUST be a terminal command that does not require the online service, MUST honour the configured store location (default local file if unset), MUST create the first administrator when none exists, MUST be idempotent if one exists, and MUST fail closed without a signing secret.
- **FR-024**: Liveness MUST succeed without an access proof and MUST NOT require a successful directory ping.
- **FR-025**: Configuration MUST come from the environment (signing secret required; store location optional with a documented default; first-admin credentials required only when creating the first administrator).

### Key Entities

- **Person**: A provisioned account with unique username, unique email, a password hash, and exactly one role. Public fields never include the password or hash.
- **Role**: Named `user` or `admin`. The coarse gate between self-only and all-people administration.
- **Permission**: A named ability (for example, read all people vs read self).
- **Role grant**: A permission given to everyone with a role.
- **Extra person grant**: A permission given to one person on top of their role; does not change the role name.
- **Access proof**: Signed snapshot issued at sign-in: identity number, role, effective permission names, issue time, expiry.
- **Default catalog**: Permissions seeded at setup and attached to `admin` and `user` as above.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A provisioned person with the correct password completes sign-in in one attempt and can state their own identity number from the success result.
- **SC-002**: After sign-in, 100% of allow/deny decisions on later requests are made without consulting the identity directory.
- **SC-003**: An ordinary member requesting another person’s record receives the same public failure whether that person exists or not (0 existence leaks in those attempts).
- **SC-004**: An administrator can complete create, read, update, and delete for another person; an ordinary member can complete those actions only for themselves.
- **SC-005**: First-time setup on an empty store produces exactly one administrator who can sign in, without the online service running.
- **SC-006**: Unknown username and wrong password are indistinguishable to an outside observer (same public failure).
- **SC-007**: After extra permissions are granted, the person’s role name is unchanged and the next sign-in carries the combined abilities.
- **SC-008**: Anyone can confirm the process is alive without signing in, even when the identity store is unreachable.

## Assumptions

- People are provisioned by an administrator in this version; there is no public self-registration.
- Access proof is a snapshot: grant changes apply on the next successful sign-in.
- First-time setup is a terminal command, not an unauthenticated register endpoint.
- Delivery is a single product cycle (analysis, design, construction with test-first, then testing).
- Peer applications share the signing secret by operational agreement; this product does not ship a second deployed peer.
- Token lifetime has a documented default until a product owner sets it (minutes, not days).
- Source of numbered product requirements remains [Requirements.md](../../Requirements.md); this spec restates journeys for planning.

## Constitution Constraints *(mandatory)*

These apply to every feature unless Complexity Tracking in the plan justifies an amendment.

- Roles MUST remain `user` and `admin` only; extra grants MUST NOT add a third role.
- Authorize MUST NOT query the identity store; JWT claims are the decision source.
- Acceptance scenarios MUST map to pytest `test_ac_*`. Gherkin `.feature` files MUST NOT be added.
- HTTP denials MUST use 401 / 403 / 404 as in Requirements.md (no existence leak).
- Secrets stay in the environment; passwords/hashes MUST NOT appear in responses.
- No new gateway, cache, broker, or IdP.
