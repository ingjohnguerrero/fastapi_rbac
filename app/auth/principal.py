"""Authenticated principal from JWT claims. No identity-store access."""

from dataclasses import dataclass

from app.auth.tokens import verify_token


@dataclass(frozen=True)
class Principal:
    user_id: int
    role: str
    permissions: frozenset[str]


def principal_from_token(token: str) -> Principal:
    payload = verify_token(token)
    perms = payload.get("permissions") or []
    if not isinstance(perms, list):
        perms = []
    return Principal(
        user_id=int(payload["sub"]),
        role=str(payload["role"]),
        permissions=frozenset(str(p) for p in perms),
    )
