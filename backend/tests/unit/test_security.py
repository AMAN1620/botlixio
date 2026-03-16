"""
Unit tests for app.core.security — password hashing + JWT.

TDD RED phase: security.py does NOT exist yet. All tests will fail.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from fastapi import HTTPException


class TestPasswordHashing:
    """UNIT-SEC-001, UNIT-SEC-002, UNIT-SEC-003"""

    def test_hash_is_different_from_input(self) -> None:  # UNIT-SEC-001
        from app.core.security import hash_password

        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 50  # bcrypt hashes are 60 chars

    def test_verify_correct_password_returns_true(self) -> None:  # UNIT-SEC-002
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_wrong_password_returns_false(self) -> None:  # UNIT-SEC-003
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_are_different(self) -> None:
        """bcrypt uses random salt — same input must not produce same hash."""
        from app.core.security import hash_password

        h1 = hash_password("mypassword123")
        h2 = hash_password("mypassword123")
        assert h1 != h2


class TestCreateAccessToken:
    """UNIT-SEC-004"""

    def test_returns_decodable_jwt_with_correct_claims(self) -> None:  # UNIT-SEC-004
        from app.core.security import create_access_token, decode_token

        token = create_access_token(user_id="abc-123", role="USER")
        payload = decode_token(token)

        assert payload["sub"] == "abc-123"
        assert payload["role"] == "USER"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_access_token_is_a_string(self) -> None:
        from app.core.security import create_access_token

        token = create_access_token(user_id="abc-123", role="USER")
        assert isinstance(token, str)
        assert len(token) > 10


class TestCreateRefreshToken:
    """UNIT-SEC-005"""

    def test_returns_jwt_with_refresh_type(self) -> None:  # UNIT-SEC-005
        from app.core.security import create_refresh_token, decode_token

        token = create_refresh_token(user_id="abc-123")
        payload = decode_token(token)

        assert payload["sub"] == "abc-123"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_returns_unique_tokens_for_same_user(self) -> None:
        from app.core.security import create_refresh_token

        token_a = create_refresh_token(user_id="abc-123")
        token_b = create_refresh_token(user_id="abc-123")

        assert token_a != token_b


class TestDecodeToken:
    """UNIT-SEC-006, UNIT-SEC-007"""

    def test_raises_401_on_expired_token(self) -> None:  # UNIT-SEC-006
        from jose import jwt
        from app.core.config import get_settings

        settings = get_settings()
        expired_payload = {
            "sub": "abc-123",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        from app.core.security import decode_token

        with pytest.raises(HTTPException) as exc:
            decode_token(expired_token)
        assert exc.value.status_code == 401

    def test_raises_401_on_tampered_token(self) -> None:  # UNIT-SEC-007
        from app.core.security import decode_token

        with pytest.raises(HTTPException) as exc:
            decode_token("not.a.valid.jwt")
        assert exc.value.status_code == 401

    def test_raises_401_on_wrong_signature(self) -> None:
        from jose import jwt

        bad_token = jwt.encode({"sub": "x"}, "wrong-secret", algorithm="HS256")
        from app.core.security import decode_token

        with pytest.raises(HTTPException) as exc:
            decode_token(bad_token)
        assert exc.value.status_code == 401


class TestHashRefreshToken:
    """hash_refresh_token must be deterministic and produce a 64-char hex string."""

    def test_produces_64_char_hex(self) -> None:
        from app.core.security import hash_refresh_token

        result = hash_refresh_token("some.jwt.token")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_same_output(self) -> None:
        from app.core.security import hash_refresh_token

        assert hash_refresh_token("token") == hash_refresh_token("token")

    def test_different_inputs_different_outputs(self) -> None:
        from app.core.security import hash_refresh_token

        assert hash_refresh_token("token-a") != hash_refresh_token("token-b")
