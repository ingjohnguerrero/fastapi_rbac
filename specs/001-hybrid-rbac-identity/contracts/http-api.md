# HTTP contract

Base: service origin. JSON UTF-8. Header for protected routes: `Authorization: Bearer <access_token>`.

Public error body: `{ "detail": "<string>" }` except FastAPI 422 validation errors.

| Status | `detail` |
| --- | --- |
| 401 | `Unauthorized` |
| 403 | `Forbidden` |
| 404 | `Not found` |
| 409 | `Conflict` |

## `POST /auth/login`

Unauthenticated. Body: `{ "username": string, "password": string }`.

| Result | Status | Body |
| --- | --- | --- |
| Success | 200 | `{ "access_token": string, "token_type": "bearer", "user_id": number }` |
| Bad credentials | 401 | Unauthorized (same for unknown user and wrong password) |
| Invalid body | 422 | validation |

JWT payload: `sub` (user id), `role`, `permissions`, `exp`, `iat`. `sub` equals `user_id`.

## `GET /health`

No token. 200 `{ "status": "ok" }`. MUST NOT ping the database.

## Users

Public fields: `id`, `username`, `email`, `role`. Never password or hash.

| Method | Path | `user` | `admin` |
| --- | --- | --- | --- |
| GET | `/users/me` | 200 own | 200 own |
| GET | `/users` | 403 | 200 list |
| POST | `/users` | 403 | 201 |
| GET | `/users/{id}` | 200 if id=`sub` else **404** | 200 or 404 |
| PATCH | `/users/{id}` | 200 if id=`sub` (no `role`); else **404** | 200 or 404; MAY set `role` |
| DELETE | `/users/{id}` | 204 if id=`sub` else **404** | 204 or 404 |

Unauthenticated on all of the above except login/health: **401**.

Create body (admin): `{ "username", "email", "password", "role": "user"|"admin" }`.

Member PATCH MUST NOT persist `role`. Cross-user object access by role `user` is **404** whether the id exists or not.

## Roles

| Method | Path | `user` | `admin` |
| --- | --- | --- | --- |
| GET | `/roles` | 403 | 200 `[{ "id", "name" }]` |
| POST | `/roles/{id}/permissions` | 403 | 200/201; body `{ "name": "items:read" }` (create permission if needed) |
| POST | `/users/{id}/permissions` | 403 | extra grant; duplicate pair rejected |

New role **names** are out of scope.

## Peer contract

A module that only has `JWT_SECRET` and the token MUST verify signature/`exp` and read `sub`/`role`/`permissions` with **zero** HTTP calls to this service.
