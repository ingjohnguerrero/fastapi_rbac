"""Password hashing (FR-06)."""

from app.auth.hashing import hash_password, verify_password


def test_hash_is_not_plaintext():
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert "secret" not in hashed


def test_verify_roundtrip():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)
