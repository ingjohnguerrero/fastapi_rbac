"""AC-FR-21 hybrid union in JWT; duplicate grants rejected."""

from fastapi.testclient import TestClient

from app.auth.tokens import verify_token
from tests.conftest import ADMIN_PASSWORD, USER_PASSWORD, login


def test_ac_fr_21_union_in_token_without_third_role(client: TestClient, seeded, settings):
    admin = login(client, "admin", ADMIN_PASSWORD).json()["access_token"]
    admin_h = {"Authorization": f"Bearer {admin}"}
    roles = {row["name"]: row["id"] for row in client.get("/roles", headers=admin_h).json()}
    user_role_id = roles["user"]
    alice_id = seeded["user_id"]

    granted_role = client.post(
        f"/roles/{user_role_id}/permissions",
        headers=admin_h,
        json={"name": "items:read"},
    )
    assert granted_role.status_code in (200, 201)
    granted_user = client.post(
        f"/users/{alice_id}/permissions",
        headers=admin_h,
        json={"name": "items:write"},
    )
    assert granted_user.status_code in (200, 201)

    dup_role = client.post(
        f"/roles/{user_role_id}/permissions",
        headers=admin_h,
        json={"name": "items:read"},
    )
    dup_user = client.post(
        f"/users/{alice_id}/permissions",
        headers=admin_h,
        json={"name": "items:write"},
    )
    assert dup_role.status_code == 409
    assert dup_user.status_code == 409

    member_forbidden = client.post(
        f"/users/{alice_id}/permissions",
        headers={"Authorization": f"Bearer {login(client, 'alice', USER_PASSWORD).json()['access_token']}"},
        json={"name": "items:admin"},
    )
    assert member_forbidden.status_code == 403

    token = login(client, "alice", USER_PASSWORD).json()["access_token"]
    payload = verify_token(token, settings=settings)
    assert payload["role"] == "user"
    assert "items:read" in payload["permissions"]
    assert "items:write" in payload["permissions"]
    assert payload["permissions"].count("items:read") == 1
