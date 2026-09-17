"""FR-12 / peer contract: verify JWT with the shared secret and zero HTTP."""

import inspect

import pytest

from app.auth.tokens import TokenError, issue_token, verify_token
from app.settings import Settings


def test_peer_jwt_zero_http_in_verifier():
    import app.auth.tokens as tokens_mod

    source = inspect.getsource(tokens_mod)
    assert "httpx" not in source
    assert "TestClient" not in source
    assert "fastapi" not in source.lower()
    assert "adapters.db" not in source


def test_peer_accepts_valid_token_and_rejects_tampered():
    settings = Settings(jwt_secret="peer-shared-secret", _env_file=None)
    token = issue_token(
        user_id=42,
        role="user",
        permissions=["users:read_self"],
        settings=settings,
    )
    payload = verify_token(token, settings=settings)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"
    assert payload["permissions"] == ["users:read_self"]

    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(TokenError):
        verify_token(tampered, settings=settings)
