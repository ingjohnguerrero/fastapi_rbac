"""Shared fixtures: temp SQLite, settings, TestClient, query counter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.adapters.db import configure_engine, create_schema, get_engine, reset_engine
from app.auth.authorize import ROLE_USER
from app.main import app
from app.models.entities import Role, User
from app.services.seed import create_first_admin, seed_catalog
from app.services.users import create_user
from app.settings import Settings, clear_settings_cache

TEST_SECRET = "test-jwt-secret-not-for-production"
ADMIN_PASSWORD = "admin-pass"
USER_PASSWORD = "user-pass"


@pytest.fixture
def settings(tmp_path, monkeypatch) -> Settings:
    db_path = tmp_path / "rbac.db"
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD)
    clear_settings_cache()
    reset_engine()
    cfg = Settings(_env_file=None)
    configure_engine(cfg)
    create_schema()
    yield cfg
    reset_engine()
    clear_settings_cache()


@pytest.fixture
def seeded(settings: Settings) -> dict:
    session = Session(get_engine())
    try:
        seed_catalog(session)
        admin = create_first_admin(
            session,
            username="admin",
            email="admin@example.com",
            password=ADMIN_PASSWORD,
        )
        member = create_user(
            session,
            username="alice",
            email="alice@example.com",
            password=USER_PASSWORD,
            role=ROLE_USER,
        )
        session.commit()
        return {"admin_id": admin.id, "user_id": member.id, "settings": settings}
    finally:
        session.close()


@pytest.fixture
def client(seeded) -> TestClient:
    return TestClient(app)


@pytest.fixture
def query_counter(settings: Settings):
    engine = get_engine()
    state = {"n": 0}

    def before(conn, cursor, statement, parameters, context, executemany):
        sql = statement.lstrip().upper()
        if sql.startswith("SELECT"):
            state["n"] += 1

    event.listen(engine, "before_cursor_execute", before)
    yield state
    event.remove(engine, "before_cursor_execute", before)


def login(client: TestClient, username: str, password: str):
    return client.post("/auth/login", json={"username": username, "password": password})


def bearer(client: TestClient, username: str, password: str) -> dict[str, str]:
    token = login(client, username, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
