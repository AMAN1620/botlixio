"""
Integration tests for auth-extended API endpoints (Phase 3).

Email verification, forgot/reset password, Google OAuth.
API-EXT-001 through API-EXT-018

Uses the same client fixture from tests/integration/conftest.py.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User

BASE = "/api/v1/auth"
VALID_REGISTER = {
    "email": "exttest@example.com",
    "password": "password123",
    "full_name": "Ext Test User",
}


# ---------------------------------------------------------------------------
# Helpers — direct DB manipulation for setting up token state
# ---------------------------------------------------------------------------

async def _register_user(client, email="exttest@example.com"):
    """Register a user and return the response."""
    return await client.post(
        f"{BASE}/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )


async def _set_user_fields(client, email, **fields):
    """Directly update user fields in DB via a raw SQL update.

    This uses the app's own get_db dependency to get a session.
    We go through the API to discover the user, then manipulate DB directly.
    """
    # Get a DB session through the app's override
    override = app.dependency_overrides.get(get_db)
    if override:
        async for session in override():
            stmt = update(User).where(User.email == email).values(**fields)
            await session.execute(stmt)
            await session.commit()
            break


async def _get_user_from_db(client, email):
    """Fetch a user from DB by email."""
    override = app.dependency_overrides.get(get_db)
    if override:
        async for session in override():
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# POST /verify-email — API-EXT-001 through API-EXT-004
# ---------------------------------------------------------------------------

class TestVerifyEmailEndpoint:
    """API-EXT-001 through API-EXT-004"""

    @pytest.mark.anyio
    async def test_valid_token_returns_200(self, client) -> None:  # API-EXT-001
        await _register_user(client)
        await _set_user_fields(
            client,
            "exttest@example.com",
            verification_token="validtoken",
            verification_token_expires=datetime.now(timezone.utc) + timedelta(hours=12),
            is_verified=False,
        )

        response = await client.post(
            f"{BASE}/verify-email", json={"token": "validtoken"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Email verified successfully"

        # Verify DB state
        user = await _get_user_from_db(client, "exttest@example.com")
        assert user.is_verified is True
        assert user.verification_token is None

    @pytest.mark.anyio
    async def test_unknown_token_returns_400(self, client) -> None:  # API-EXT-002
        response = await client.post(
            f"{BASE}/verify-email", json={"token": "nonexistent"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid token"

    @pytest.mark.anyio
    async def test_expired_token_returns_400(self, client) -> None:  # API-EXT-003
        await _register_user(client)
        await _set_user_fields(
            client,
            "exttest@example.com",
            verification_token="expiredtoken",
            verification_token_expires=datetime.now(timezone.utc) - timedelta(hours=25),
            is_verified=False,
        )

        response = await client.post(
            f"{BASE}/verify-email", json={"token": "expiredtoken"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Token expired"

    @pytest.mark.anyio
    async def test_already_verified_returns_400(self, client) -> None:  # API-EXT-004
        await _register_user(client)
        await _set_user_fields(
            client,
            "exttest@example.com",
            verification_token="validtoken",
            verification_token_expires=datetime.now(timezone.utc) + timedelta(hours=12),
            is_verified=True,
        )

        response = await client.post(
            f"{BASE}/verify-email", json={"token": "validtoken"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already verified"


# ---------------------------------------------------------------------------
# POST /forgot-password — API-EXT-005 through API-EXT-007
# ---------------------------------------------------------------------------

class TestForgotPasswordEndpoint:
    """API-EXT-005 through API-EXT-007"""

    @pytest.mark.anyio
    async def test_existing_email_returns_200(self, client) -> None:  # API-EXT-005
        await _register_user(client, "forgotuser@example.com")

        with patch("app.services.auth_service.EmailService", autospec=True):
            response = await client.post(
                f"{BASE}/forgot-password",
                json={"email": "forgotuser@example.com"},
            )

        assert response.status_code == 200
        assert "If that email exists" in response.json()["message"]

        # Verify reset token was set
        user = await _get_user_from_db(client, "forgotuser@example.com")
        assert user.reset_token is not None
        assert user.reset_token_expires is not None

    @pytest.mark.anyio
    async def test_unknown_email_returns_200_no_enumeration(self, client) -> None:  # API-EXT-006
        response = await client.post(
            f"{BASE}/forgot-password",
            json={"email": "nobody@example.com"},
        )
        assert response.status_code == 200
        assert "If that email exists" in response.json()["message"]

    @pytest.mark.anyio
    async def test_invalid_email_format_returns_422(self, client) -> None:  # API-EXT-007
        response = await client.post(
            f"{BASE}/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /reset-password — API-EXT-008 through API-EXT-011
# ---------------------------------------------------------------------------

class TestResetPasswordEndpoint:
    """API-EXT-008 through API-EXT-011"""

    @pytest.mark.anyio
    async def test_valid_token_updates_password(self, client) -> None:  # API-EXT-008
        await _register_user(client, "resetuser@example.com")
        await _set_user_fields(
            client,
            "resetuser@example.com",
            reset_token="resettoken",
            reset_token_expires=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

        response = await client.post(
            f"{BASE}/reset-password",
            json={"token": "resettoken", "new_password": "newsecure123"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset successfully"

        # Verify reset token cleared and sessions invalidated (check BEFORE next login)
        user = await _get_user_from_db(client, "resetuser@example.com")
        assert user.reset_token is None
        assert user.refresh_token_hash is None

        # Verify new password works
        login_response = await client.post(
            f"{BASE}/login",
            json={"email": "resetuser@example.com", "password": "newsecure123"},
        )
        assert login_response.status_code == 200

        # Verify old password doesn't work
        old_login = await client.post(
            f"{BASE}/login",
            json={"email": "resetuser@example.com", "password": "password123"},
        )
        assert old_login.status_code == 401

    @pytest.mark.anyio
    async def test_unknown_token_returns_400(self, client) -> None:  # API-EXT-009
        response = await client.post(
            f"{BASE}/reset-password",
            json={"token": "badtoken", "new_password": "newsecure123"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid reset token"

    @pytest.mark.anyio
    async def test_expired_token_returns_400(self, client) -> None:  # API-EXT-010
        await _register_user(client, "expiredresetuser@example.com")
        await _set_user_fields(
            client,
            "expiredresetuser@example.com",
            reset_token="expiredtoken",
            reset_token_expires=datetime.now(timezone.utc) - timedelta(hours=2),
        )

        response = await client.post(
            f"{BASE}/reset-password",
            json={"token": "expiredtoken", "new_password": "newsecure123"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Reset link has expired"

    @pytest.mark.anyio
    async def test_short_password_returns_422(self, client) -> None:  # API-EXT-011
        response = await client.post(
            f"{BASE}/reset-password",
            json={"token": "anytoken", "new_password": "short"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /auth/google — API-EXT-012
# ---------------------------------------------------------------------------

class TestGoogleOAuthRedirect:
    """API-EXT-012"""

    @pytest.mark.anyio
    async def test_redirects_to_google_consent_url(self, client) -> None:  # API-EXT-012
        response = await client.get(f"{BASE}/google", follow_redirects=False)

        assert response.status_code == 302
        location = response.headers["location"]
        assert "accounts.google.com" in location
        assert "client_id" in location
        assert "redirect_uri" in location
        assert "scope" in location


# ---------------------------------------------------------------------------
# GET /auth/google/callback — API-EXT-013 through API-EXT-016
# ---------------------------------------------------------------------------

GOOGLE_USERINFO = {
    "email": "oauthuser@gmail.com",
    "name": "OAuth User",
    "id": "google_test_123",
    "picture": "https://lh3.googleusercontent.com/photo",
}


class TestGoogleOAuthCallback:
    """API-EXT-013 through API-EXT-016"""

    def _mock_google_apis(self, userinfo=None):
        """Patch the Google token exchange and userinfo at the service level."""
        info = userinfo or GOOGLE_USERINFO
        return patch(
            "app.services.auth_service.AuthService._exchange_google_code",
            new_callable=AsyncMock,
            return_value=info,
        )

    @pytest.mark.anyio
    async def test_valid_code_creates_user_and_redirects(self, client) -> None:  # API-EXT-013
        with self._mock_google_apis():
            response = await client.get(
                f"{BASE}/google/callback?code=valid_code",
                follow_redirects=False,
            )

        assert response.status_code == 302
        location = response.headers["location"]
        settings = get_settings()
        assert location.startswith(settings.FRONTEND_URL)
        assert "access_token=" in location
        assert "refresh_token=" in location

        # Verify user created in DB
        user = await _get_user_from_db(client, "oauthuser@gmail.com")
        assert user is not None
        assert user.auth_provider.value == "google" or str(user.auth_provider) == "GOOGLE"
        assert user.is_verified is True

    @pytest.mark.anyio
    async def test_existing_oauth_user_logs_in_and_redirects(self, client) -> None:  # API-EXT-014
        # First login creates the user
        with self._mock_google_apis():
            await client.get(
                f"{BASE}/google/callback?code=valid_code",
                follow_redirects=False,
            )

        # Second login should log in, not create
        with self._mock_google_apis():
            response = await client.get(
                f"{BASE}/google/callback?code=valid_code",
                follow_redirects=False,
            )

        assert response.status_code == 302
        assert "access_token=" in response.headers["location"]

        # last_login_at should be updated
        user = await _get_user_from_db(client, "oauthuser@gmail.com")
        assert user.last_login_at is not None

    @pytest.mark.anyio
    async def test_email_conflict_with_local_user_returns_400(self, client) -> None:  # API-EXT-015
        # Register a LOCAL user with same email
        await _register_user(client, "oauthuser@gmail.com")

        with self._mock_google_apis():
            response = await client.get(
                f"{BASE}/google/callback?code=valid_code",
                follow_redirects=False,
            )

        assert response.status_code == 400
        assert "Account exists with email/password" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_invalid_code_returns_400(self, client) -> None:  # API-EXT-016
        with patch(
            "app.services.auth_service.AuthService._exchange_google_code",
            new_callable=AsyncMock,
            side_effect=Exception("invalid_grant"),
        ):
            response = await client.get(
                f"{BASE}/google/callback?code=bad_code",
                follow_redirects=False,
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "OAuth authentication failed"


# ---------------------------------------------------------------------------
# Route Registration — API-EXT-017
# ---------------------------------------------------------------------------

class TestRouteRegistration:
    """API-EXT-017"""

    @pytest.mark.anyio
    async def test_all_phase3_endpoints_are_registered(self, client) -> None:  # API-EXT-017
        # Each endpoint should return something other than 404.
        # They may return 400/422 for missing body — that's fine.

        verify = await client.post(f"{BASE}/verify-email", json={})
        assert verify.status_code != 404

        forgot = await client.post(f"{BASE}/forgot-password", json={})
        assert forgot.status_code != 404

        reset = await client.post(f"{BASE}/reset-password", json={})
        assert reset.status_code != 404

        google = await client.get(f"{BASE}/google", follow_redirects=False)
        assert google.status_code != 404

        callback = await client.get(f"{BASE}/google/callback", follow_redirects=False)
        assert callback.status_code != 404


# ---------------------------------------------------------------------------
# Anti-Enumeration Timing — API-EXT-018
# ---------------------------------------------------------------------------

class TestAntiEnumerationTiming:
    """API-EXT-018"""

    @pytest.mark.anyio
    async def test_forgot_password_timing_is_consistent(self, client) -> None:  # API-EXT-018
        # Register a known user
        await _register_user(client, "known@example.com")

        # Time the known-email request
        start_known = time.monotonic()
        resp_known = await client.post(
            f"{BASE}/forgot-password",
            json={"email": "known@example.com"},
        )
        time_known = time.monotonic() - start_known

        # Time the unknown-email request
        start_unknown = time.monotonic()
        resp_unknown = await client.post(
            f"{BASE}/forgot-password",
            json={"email": "unknown@example.com"},
        )
        time_unknown = time.monotonic() - start_unknown

        # Both must return 200 with identical body shape
        assert resp_known.status_code == 200
        assert resp_unknown.status_code == 200
        assert resp_known.json()["message"] == resp_unknown.json()["message"]

        # Response times should be within 200ms of each other
        delta = abs(time_known - time_unknown)
        assert delta < 0.200, (
            f"Timing difference {delta:.3f}s may leak user existence "
            f"(known={time_known:.3f}s, unknown={time_unknown:.3f}s)"
        )
