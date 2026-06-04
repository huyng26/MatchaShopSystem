from uuid import uuid4

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_verification() -> None:
    hashed_password = hash_password("strong-password")

    assert hashed_password != "strong-password"
    assert verify_password("strong-password", hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_access_and_refresh_tokens_include_expected_claims() -> None:
    user_id = uuid4()

    access_payload = decode_token(create_access_token(user_id, "admin"))
    refresh_payload = decode_token(create_refresh_token(user_id))

    assert access_payload["sub"] == str(user_id)
    assert access_payload["type"] == "access"
    assert access_payload["role"] == "admin"
    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["type"] == "refresh"


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(AuthenticationError):
        decode_token("not-a-valid-token")
