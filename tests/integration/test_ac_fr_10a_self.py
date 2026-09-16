"""AC-FR-10a, AC-FR-10b, AC-FR-10c."""

from fastapi.testclient import TestClient

from tests.conftest import ADMIN_PASSWORD, USER_PASSWORD, login


def _alice(client: TestClient) -> tuple[dict[str, str], int]:
    body = login(client, "alice", USER_PASSWORD).json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user_id"]


def test_ac_fr_10b_self_read(client: TestClient):
    headers, alice_id = _alice(client)
    me = client.get("/users/me", headers=headers)
    own = client.get(f"/users/{alice_id}", headers=headers)
    assert me.status_code == 200
    assert own.status_code == 200
    assert me.json()["id"] == own.json()["id"] == alice_id
    assert me.json()["username"] == "alice"
    assert me.json()["role"] == "user"
    assert "hashed_password" not in me.json()


def test_ac_fr_10a_cross_user_is_404_whether_or_not_exists(client: TestClient, seeded):
    headers, alice_id = _alice(client)
    admin_id = seeded["admin_id"]
    assert admin_id != alice_id
    existing = client.get(f"/users/{admin_id}", headers=headers)
    missing = client.get("/users/999999", headers=headers)
    assert existing.status_code == 404
    assert missing.status_code == 404
    assert existing.json() == missing.json()
    assert existing.json()["detail"] == "Not found"

    patch_other = client.patch(
        f"/users/{admin_id}",
        headers=headers,
        json={"email": "hacked@example.com"},
    )
    delete_other = client.delete(f"/users/{admin_id}", headers=headers)
    assert patch_other.status_code == 404
    assert delete_other.status_code == 404
    assert patch_other.json()["detail"] == delete_other.json()["detail"] == "Not found"

    admin_token = login(client, "admin", ADMIN_PASSWORD).json()["access_token"]
    still = client.get(
        f"/users/{admin_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert still.status_code == 200


def test_ac_fr_10c_member_patch_email_but_not_role(client: TestClient):
    headers, alice_id = _alice(client)
    patched = client.patch(
        f"/users/{alice_id}",
        headers=headers,
        json={"email": "alice-new@example.com"},
    )
    assert patched.status_code == 200
    assert patched.json()["email"] == "alice-new@example.com"
    assert patched.json()["role"] == "user"

    role_attempt = client.patch(
        f"/users/{alice_id}",
        headers=headers,
        json={"role": "admin"},
    )
    assert role_attempt.status_code == 422
    still = client.get("/users/me", headers=headers)
    assert still.json()["role"] == "user"
