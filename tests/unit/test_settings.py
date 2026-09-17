"""AC: JWT_SECRET required."""

import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_settings_fail_closed_without_jwt_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_fail_closed_with_empty_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(jwt_secret="", _env_file=None)


def test_settings_fail_closed_with_whitespace_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(jwt_secret="   ", _env_file=None)
