# Data model: Hybrid RBAC identity

Logical model aligned with [Requirements.md](../../Requirements.md) §5 and vision VD-001. Physical types are SQLAlchemy / SQLite-default.

## Entities

### User

| Field | Type | Rules |
| --- | --- | --- |
| id | integer PK | Identity number; JWT `sub`; login `user_id` |
| username | string | Unique, required |
| email | string | Unique, required |
| hashed_password | string | One-way hash; never in API bodies |
| role_id | integer FK → Role.id | NOT NULL; exactly one role |

No string `role` column as source of truth. Catalog name is read via join at login.

### Role

| Field | Type | Rules |
| --- | --- | --- |
| id | integer PK | |
| name | string | Unique, NOT NULL; `name ∈ {user, admin}` |

### Permission

| Field | Type | Rules |
| --- | --- | --- |
| id | integer PK | |
| name | string | Unique, NOT NULL; stable codes (default catalog below) |

Extra codes (e.g. `items:read`) MAY be inserted later for hybrid overlay tests.

### roles_permissions (role grant)

| Field | Rules |
| --- | --- |
| role_id | FK Role, part of unique pair |
| permission_id | FK Permission, part of unique pair |

Role **1** — **0..\*** grants.

### users_permissions (extra user grant)

| Field | Rules |
| --- | --- |
| user_id | FK User, part of unique pair |
| permission_id | FK Permission, part of unique pair |

User **1** — **0..\*** extra grants. Extra grants MUST NOT change `User.role_id`.

## Relationships

- User **\*** — **1** Role
- Role **1** — **0..\*** Permission (via roles_permissions)
- User **1** — **0..\*** Permission (via users_permissions)

Effective permissions at login = role grants ∪ extra user grants (duplicate names collapse).

## Default catalog (seeded at init)

| name | admin | user |
| --- | --- | --- |
| `users:create` | yes | no |
| `users:read` | yes | no |
| `users:update` | yes | no |
| `users:delete` | yes | no |
| `users:read_self` | yes | yes |
| `users:update_self` | yes | yes |
| `users:delete_self` | yes | yes |
| `roles:read` | yes | no |
| `roles:grant` | yes | no |
| `users:grant` | yes | no |

## Validation

- Assigning role name other than `user`/`admin` → 422 or 400, no row
- Duplicate username/email → 409
- Duplicate grant pair → reject (409 or 422)
- Public User DTO: `id`, `username`, `email`, `role` (catalog name). Never hash.

## State / snapshot

No workflow states on User. Access proof is a **snapshot**: grant changes apply on the next successful login.
