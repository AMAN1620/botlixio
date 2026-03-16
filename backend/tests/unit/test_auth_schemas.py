"""
Unit tests for app.schemas.auth — Pydantic request/response schemas.

TDD RED phase: schemas/auth.py does NOT exist yet. All tests will fail.
"""

import pytest
from pydantic import ValidationError


class TestRegisterRequest:
    """UNIT-SCHEMA-001, UNIT-SCHEMA-002, UNIT-SCHEMA-003"""

    def test_rejects_invalid_email(self) -> None:  # UNIT-SCHEMA-001
        from app.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="password123", full_name="Test")

    def test_rejects_password_under_8_chars(self) -> None:  # UNIT-SCHEMA-001
        from app.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="1234567", full_name="Test")

    def test_rejects_empty_full_name(self) -> None:  # UNIT-SCHEMA-002
        from app.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="password123", full_name="")

    def test_accepts_valid_inputs(self) -> None:  # UNIT-SCHEMA-003
        from app.schemas.auth import RegisterRequest

        req = RegisterRequest(
            email="test@example.com",
            password="password123",
            full_name="Test User",
        )
        assert req.email == "test@example.com"
        assert req.password == "password123"
        assert req.full_name == "Test User"

    def test_rejects_password_over_128_chars(self) -> None:
        from app.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="a" * 129,
                full_name="Test",
            )


class TestLoginRequest:
    """UNIT-SCHEMA-004"""

    def test_rejects_empty_password(self) -> None:  # UNIT-SCHEMA-004
        from app.schemas.auth import LoginRequest

        with pytest.raises(ValidationError):
            LoginRequest(email="test@example.com", password="")

    def test_accepts_valid_login(self) -> None:
        from app.schemas.auth import LoginRequest

        req = LoginRequest(email="test@example.com", password="any")
        assert req.email == "test@example.com"


class TestTokenResponse:
    """TokenResponse must have access_token, refresh_token, token_type."""

    def test_token_type_defaults_to_bearer(self) -> None:
        from app.schemas.auth import TokenResponse

        resp = TokenResponse(access_token="acc", refresh_token="ref")
        assert resp.token_type == "bearer"


class TestUserResponse:
    """UserResponse must build from SQLAlchemy model attributes (from_attributes=True)."""

    def test_from_attributes_config_is_set(self) -> None:
        from app.schemas.auth import UserResponse

        assert UserResponse.model_config.get("from_attributes") is True
