from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("SecurePass123!")
    assert hashed != "SecurePass123!"
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_and_refresh_tokens_have_correct_type():
    user_id = "11111111-1111-1111-1111-111111111111"
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    access_payload = decode_token(access, expected_type="access")
    refresh_payload = decode_token(refresh, expected_type="refresh")

    assert access_payload["sub"] == user_id
    assert refresh_payload["sub"] == user_id
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"


def test_decode_rejects_wrong_token_type():
    token = create_access_token("11111111-1111-1111-1111-111111111111")
    try:
        decode_token(token, expected_type="refresh")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Incorrect token type" in str(exc)
