"""
Integration tests for /api/v1/auth/* endpoints.

Uses httpx.AsyncClient with the real FastAPI app and a fresh DB per test.
Fixtures (client, db_session) are provided by tests/integration/conftest.py.
"""

import pytest
from datetime import datetime, timezone, timedelta

BASE = "/api/v1/auth"
VALID_REGISTER = {
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
}


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

class TestRegisterEndpoint:

    @pytest.mark.anyio
    async def test_register_success_returns_201(self, client) -> None:  # API-AUTH-001
        response = await client.post(f"{BASE}/register", json=VALID_REGISTER)
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["data"]["email"] == VALID_REGISTER["email"]
        assert "password" not in data["data"]
        assert "password_hash" not in data["data"]

    @pytest.mark.anyio
    async def test_register_duplicate_email_returns_409(self, client) -> None:  # API-AUTH-002
        # First registration
        await client.post(f"{BASE}/register", json=VALID_REGISTER)
        # Second with same email
        response = await client.post(f"{BASE}/register", json=VALID_REGISTER)
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_register_invalid_input_returns_422(self, client) -> None:  # API-AUTH-003
        response = await client.post(
            f"{BASE}/register",
            json={"email": "invalid", "password": "short"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

class TestLoginEndpoint:

    @pytest.mark.anyio
    async def test_login_success_returns_200_with_tokens(self, client) -> None:  # API-AUTH-004
        # Register first
        await client.post(f"{BASE}/register", json=VALID_REGISTER)
        # Login
        response = await client.post(
            f"{BASE}/login",
            json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.anyio
    async def test_login_wrong_password_returns_401(self, client) -> None:  # API-AUTH-005
        await client.post(f"{BASE}/register", json=VALID_REGISTER)
        response = await client.post(
            f"{BASE}/login",
            json={"email": VALID_REGISTER["email"], "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    @pytest.mark.anyio
    async def test_login_unknown_email_returns_401(self, client) -> None:  # API-AUTH-006
        response = await client.post(
            f"{BASE}/login",
            json={"email": "nobody@example.com", "password": "any"},
        )
        assert response.status_code == 401
        # Must be same generic message — no email enumeration
        assert response.json()["detail"] == "Invalid credentials"


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

class TestMeEndpoint:

    @pytest.fixture
    async def auth_token(self, client):
        """Register + login, return access token."""
        await client.post(f"{BASE}/register", json=VALID_REGISTER)
        resp = await client.post(
            f"{BASE}/login",
            json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
        )
        return resp.json()["access_token"]

    @pytest.mark.anyio
    async def test_me_with_valid_token_returns_200(self, client, auth_token) -> None:  # API-AUTH-007
        response = await client.get(
            f"{BASE}/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == VALID_REGISTER["email"]
        assert "password_hash" not in data

    @pytest.mark.anyio
    async def test_me_without_token_returns_401(self, client) -> None:  # API-AUTH-008
        response = await client.get(f"{BASE}/me")
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_me_with_expired_token_returns_401(self, client) -> None:  # API-AUTH-009
        from jose import jwt
        from datetime import datetime, timezone, timedelta
        from app.core.config import get_settings

        settings = get_settings()
        expired_token = jwt.encode(
            {
                "sub": "abc-123",
                "role": "USER",
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        response = await client.get(
            f"{BASE}/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

class TestRefreshEndpoint:

    @pytest.fixture
    async def tokens(self, client):
        """Register + login, return both tokens."""
        await client.post(f"{BASE}/register", json=VALID_REGISTER)
        resp = await client.post(
            f"{BASE}/login",
            json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
        )
        return resp.json()

    @pytest.mark.anyio
    async def test_refresh_success_returns_new_tokens(self, client, tokens) -> None:  # API-AUTH-010
        response = await client.post(
            f"{BASE}/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # Old refresh token must now be rejected (rotation enforced)
        reuse_response = await client.post(
            f"{BASE}/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert reuse_response.status_code == 401

    @pytest.mark.anyio
    async def test_refresh_with_invalid_token_returns_401(self, client) -> None:  # API-AUTH-011
        response = await client.post(
            f"{BASE}/refresh",
            json={"refresh_token": "garbage.jwt.token"},
        )
        assert response.status_code == 401
