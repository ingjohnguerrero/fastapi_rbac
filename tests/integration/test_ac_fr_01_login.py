"""AC-FR-01, AC-FR-03, AC-FR-07."""

from fastapi.testclient import TestClient

from app.auth.tokens import verify_token
from tests.conftest import USER_PASSWORD, login


def test_ac_fr_01_login_returns_token_and_user_id(client: TestClient, seeded, settings):
    response = login(client, "alice", USER_PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user_id"] == seeded["user_id"]
    payload = verify_token(body["access_token"], settings=settings)
    assert payload["sub"] == str(body["user_id"])
    assert payload["role"] == "user"
    assert "permissions" in payload


def test_ac_fr_03_unknown_user_and_wrong_password_share_detail(client: TestClient):
    wrong = login(client, "alice", "not-the-password")
    unknown = login(client, "does-not-exist", USER_PASSWORD)
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"] == "Unauthorized"


def test_ac_fr_07_one_credential_select(client: TestClient, query_counter):
    query_counter["n"] = 0
    response = login(client, "alice", USER_PASSWORD)
    assert response.status_code == 200
    assert query_counter["n"] == 1
