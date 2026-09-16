"""HS256 JWT issue and verify. This module MUST NOT import the identity store."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.settings import Settings, get_settings

REQUIRED_CLAIMS = ("sub", "role", "permissions", "exp", "iat")


class TokenError(Exception):
    """Invalid, expired, or malformed token."""


def issue_token(
    *,
    user_id: int,
    role: str,
    permissions: list[str],
    settings: Settings | None = None,
) -> str:
    cfg = settings or get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "permissions": list(permissions),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=cfg.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def verify_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.jwt_secret,
            algorithms=[cfg.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise TokenError("invalid token") from exc
    if any(claim not in payload for claim in REQUIRED_CLAIMS):
        raise TokenError("invalid token")
    return payload
