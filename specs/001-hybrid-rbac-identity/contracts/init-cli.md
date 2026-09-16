# Init CLI contract

Not an HTTP route. MUST NOT require uvicorn to be running.

## Invocation

```bash
python -m app.cli init
# equivalent: ./scripts/init.sh
```

## Environment

| Variable | Required | Default |
| --- | --- | --- |
| `JWT_SECRET` | **Yes** | — (fail closed if missing) |
| `DATABASE_URL` | No | `sqlite:///./rbac.db` |
| `ADMIN_USERNAME` | When no admin exists | — |
| `ADMIN_EMAIL` | When no admin exists | — |
| `ADMIN_PASSWORD` | When no admin exists | — |

A provided `DATABASE_URL` MUST be used as-is (never silently ignored).

## Behaviour

1. Connect with the resolved URL.
2. Create or migrate schema (users, roles, permissions, grant tables).
3. Seed roles `user` and `admin`.
4. Seed default permission catalog and `roles_permissions` (see data-model.md).
5. If no user with role `admin` exists: require `ADMIN_*`, hash the password, insert admin.
6. If an admin exists: skip insert; do **not** overwrite password; exit 0.
7. Print resolved store URL **without secrets** and a success or error summary.

## Exit codes

| Code | When |
| --- | --- |
| 0 | Success, including idempotent skip |
| non-zero | Missing `JWT_SECRET`; store unreachable; `ADMIN_*` missing when first admin must be created |
