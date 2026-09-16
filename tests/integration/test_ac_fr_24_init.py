"""AC-FR-24, AC-FR-25, AC-FR-28, AC-FR-29, AC-FR-21a."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.adapters.db import reset_engine
from app.auth.hashing import verify_password
from app.auth.authorize import (
    ADMIN_GRANTS,
    USER_GRANTS,
    USERS_CREATE,
    USERS_DELETE,
    USERS_READ,
    USERS_UPDATE,
)
from app.cli import main, run_init
from app.main import app
from app.models.entities import Role, User
from app.settings import Settings, clear_settings_cache

SECRET = "init-test-secret"
ADMIN_PASSWORD = "first-admin-pass"


def _settings(db_path: Path, *, admin: bool = True) -> Settings:
    kwargs = {
        "jwt_secret": SECRET,
        "database_url": f"sqlite:///{db_path}",
        "_env_file": None,
    }
    if admin:
        kwargs.update(
            admin_username="admin",
            admin_email="admin@example.com",
            admin_password=ADMIN_PASSWORD,
        )
    return Settings(**kwargs)


def test_ac_fr_24_init_creates_admin_and_allows_login(tmp_path, monkeypatch):
    db_path = tmp_path / "store.db"
    cfg = _settings(db_path)
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("DATABASE_URL", cfg.database_url)
    clear_settings_cache()
    reset_engine()
    assert run_init(cfg) == 0
    assert db_path.exists()

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    reset_engine()
    clear_settings_cache()


def test_ac_fr_21a_default_catalog(tmp_path):
    db_path = tmp_path / "store.db"
    cfg = _settings(db_path)
    reset_engine()
    assert run_init(cfg) == 0
    engine = create_engine(cfg.database_url)
    session = Session(engine)
    try:
        roles = {r.name: r for r in session.scalars(select(Role)).all()}
        assert set(roles) == {"user", "admin"}
        admin_perms = {p.name for p in roles["admin"].permissions}
        user_perms = {p.name for p in roles["user"].permissions}
        for name in (USERS_CREATE, USERS_READ, USERS_UPDATE, USERS_DELETE):
            assert name in admin_perms
        assert admin_perms == set(ADMIN_GRANTS)
        assert user_perms == set(USER_GRANTS)
    finally:
        session.close()
        engine.dispose()
        reset_engine()


def test_ac_fr_25_honours_custom_sqlite_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    default_db = tmp_path / "rbac.db"
    custom_db = tmp_path / "custom.db"
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.db")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD)
    clear_settings_cache()
    reset_engine()
    assert main(["init"]) == 0
    assert custom_db.exists()
    assert not default_db.exists()
    reset_engine()
    clear_settings_cache()


def test_ac_fr_28_second_init_skips_password_change(tmp_path):
    db_path = tmp_path / "store.db"
    cfg = _settings(db_path)
    reset_engine()
    assert run_init(cfg) == 0
    engine = create_engine(cfg.database_url)
    session = Session(engine)
    hashed = session.scalar(select(User).where(User.username == "admin")).hashed_password
    session.close()
    engine.dispose()

    other = cfg.model_copy(update={"admin_password": "a-different-password"})
    reset_engine()
    assert run_init(other) == 0

    engine = create_engine(cfg.database_url)
    session = Session(engine)
    user = session.scalar(select(User).where(User.username == "admin"))
    assert user.hashed_password == hashed
    assert verify_password(ADMIN_PASSWORD, user.hashed_password)
    assert not verify_password("a-different-password", user.hashed_password)
    session.close()
    engine.dispose()
    reset_engine()


def test_ac_fr_29_missing_jwt_secret_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'rbac.db'}")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD)
    clear_settings_cache()
    reset_engine()
    assert main(["init"]) != 0
    assert not (tmp_path / "rbac.db").exists()
    reset_engine()
    clear_settings_cache()


def test_ac_fr_29_missing_admin_env_when_empty_store(tmp_path):
    db_path = tmp_path / "store.db"
    cfg = _settings(db_path, admin=False)
    reset_engine()
    assert run_init(cfg) != 0
    engine = create_engine(cfg.database_url)
    session = Session(engine)
    assert session.scalar(select(User)) is None
    session.close()
    engine.dispose()
    reset_engine()
