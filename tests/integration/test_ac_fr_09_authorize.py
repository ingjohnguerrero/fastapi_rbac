"""AC-FR-09, AC-FR-10."""

from fastapi.testclient import TestClient

from tests.conftest import USER_PASSWORD, login


def test_ac_fr_09_missing_token_is_unauthorized(client: TestClient, query_counter):
    query_counter["n"] = 0
    response = client.get("/users")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"
    assert query_counter["n"] == 0


def test_ac_fr_10_member_cannot_list_users(client: TestClient, query_counter):
    token = login(client, "alice", USER_PASSWORD).json()["access_token"]
    query_counter["n"] = 0
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"
    assert query_counter["n"] == 0
