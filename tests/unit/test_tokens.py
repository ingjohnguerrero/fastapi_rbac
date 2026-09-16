"""JWT issue/verify with no identity-store import (FR-04, FR-09)."""

import inspect
import time

import pytest

import app.auth.tokens as tokens_mod
from app.auth.tokens import TokenError, issue_token, verify_token
from app.settings import Settings


def test_tokens_module_does_not_import_store():
    source = inspect.getsource(tokens_mod)
    assert "adapters.db" not in source
    assert "models.entities" not in source


def test_issue_and_verify():
    settings = Settings(jwt_secret="unit-secret", _env_file=None)
    token = issue_token(user_id=7, role="user", permissions=["users:read_self"], settings=settings)
    payload = verify_token(token, settings=settings)
    assert payload["sub"] == "7"
    assert payload["role"] == "user"
    assert payload["permissions"] == ["users:read_self"]
    assert "exp" in payload and "iat" in payload


def test_bad_signature_fail_closed():
    settings = Settings(jwt_secret="unit-secret", _env_file=None)
    other = Settings(jwt_secret="other-secret", _env_file=None)
    token = issue_token(user_id=1, role="admin", permissions=[], settings=settings)
    with pytest.raises(TokenError):
        verify_token(token, settings=other)


def test_expired_fail_closed():
    settings = Settings(
        jwt_secret="unit-secret",
        access_token_expire_minutes=0,
        _env_file=None,
    )
    token = issue_token(user_id=1, role="user", permissions=[], settings=settings)
    time.sleep(1.1)
    with pytest.raises(TokenError):
        verify_token(token, settings=settings)
