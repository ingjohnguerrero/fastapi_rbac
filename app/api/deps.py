"""FastAPI dependencies: Bearer principal and permission gates. No store on authorize."""

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.errors import forbidden, unauthorized
from app.auth.authorize import has_permission
from app.auth.principal import Principal, principal_from_token
from app.auth.tokens import TokenError

_bearer = HTTPBearer(auto_error=False)


def get_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        unauthorized()
    try:
        return principal_from_token(creds.credentials)
    except (TokenError, ValueError, KeyError, TypeError):
        unauthorized()
    raise AssertionError("unreachable")


def require_permission(name: str) -> Callable[[Principal], Principal]:
    def _dep(principal: Principal = Depends(get_principal)) -> Principal:
        if not has_permission(principal, name):
            forbidden()
        return principal

    return _dep
