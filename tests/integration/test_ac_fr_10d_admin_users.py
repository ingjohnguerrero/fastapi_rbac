"""AC-FR-10d, AC-FR-14, AC-FR-16."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.db import get_engine
from app.models.entities import User
from tests.conftest import ADMIN_PASSWORD, USER_PASSWORD, login


def _admin_headers(client: TestClient) -> dict[str, str]:
    token = login(client, "admin", ADMIN_PASSWORD).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _member_headers(client: TestClient) -> dict[str, str]:
    token = login(client, "alice", USER_PASSWORD).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ac_fr_10d_admin_crud_another_user(client: TestClient):
    headers = _admin_headers(client)
    created = client.post(
        "/users",
        headers=headers,
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "bob-pass",
            "role": "user",
        },
    )
    assert created.status_code == 201
    bob_id = created.json()["id"]
    assert created.json()["role"] == "user"
    assert "hashed_password" not in created.json()
    assert "password" not in created.json()

    listed = client.get("/users", headers=headers)
    assert listed.status_code == 200
    ids = {row["id"] for row in listed.json()}
    assert bob_id in ids

    patched = client.patch(
        f"/users/{bob_id}",
        headers=headers,
        json={"email": "bob2@example.com"},
    )
    assert patched.status_code == 200
    assert patched.json()["email"] == "bob2@example.com"

    deleted = client.delete(f"/users/{bob_id}", headers=headers)
    assert deleted.status_code == 204
    missing = client.get(f"/users/{bob_id}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Not found"

    roles = client.get("/roles", headers=headers)
    assert roles.status_code == 200
    assert {row["name"] for row in roles.json()} == {"user", "admin"}


def test_ac_fr_14_invalid_role_not_inserted(client: TestClient):
    headers = _admin_headers(client)
    session = Session(get_engine())
    before = session.scalar(select(func.count()).select_from(User))
    session.close()
    response = client.post(
        "/users",
        headers=headers,
        json={
            "username": "eve",
            "email": "eve@example.com",
            "password": "eve-pass",
            "role": "superadmin",
        },
    )
    assert response.status_code in (400, 422)
    session = Session(get_engine())
    after = session.scalar(select(func.count()).select_from(User))
    session.close()
    assert after == before


def test_ac_fr_16_duplicate_username_conflict(client: TestClient):
    headers = _admin_headers(client)
    response = client.post(
        "/users",
        headers=headers,
        json={
            "username": "alice",
            "email": "alice-dup@example.com",
            "password": "x",
            "role": "user",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Conflict"


def test_member_cannot_create_or_list(client: TestClient):
    headers = _member_headers(client)
    listed = client.get("/users", headers=headers)
    assert listed.status_code == 403
    created = client.post(
        "/users",
        headers=headers,
        json={
            "username": "carol",
            "email": "carol@example.com",
            "password": "x",
            "role": "user",
        },
    )
    assert created.status_code == 403
    assert created.json()["detail"] == "Forbidden"
