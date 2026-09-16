"""AC: JWT_SECRET required."""

import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_settings_fail_closed_without_jwt_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
