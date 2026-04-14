"""
Unit tests for auth-extended service methods — email verification, forgot/reset
password, Google OAuth, and registration update.

All tests mock the repository and email service layers.
SVC-EXT-001 through SVC-EXT-023
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.enums import AuthProvider, UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(**kwargs):
    """Build a mock User object with sensible defaults."""
    user = MagicMock()
    user.id = kwargs.get("id", uuid.uuid4())
    user.email = kwargs.get("email", "test@example.com")
    user.full_name = kwargs.get("full_name", "Test User")
    user.password_hash = kwargs.get("password_hash", "$2b$12$hashedpassword")
    user.is_active = kwargs.get("is_active", True)
    user.is_verified = kwargs.get("is_verified", False)
    user.auth_provider = kwargs.get("auth_provider", AuthProvider.LOCAL)
    user.role = kwargs.get("role", UserRole.USER)
    user.refresh_token_hash = kwargs.get("refresh_token_hash", None)
    user.avatar_url = kwargs.get("avatar_url", None)
    user.last_login_at = kwargs.get("last_login_at", None)
    user.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    user.verification_token = kwargs.get("verification_token", None)
    user.verification_token_expires = kwargs.get("verification_token_expires", None)
    user.reset_token = kwargs.get("reset_token", None)
    user.reset_token_expires = kwargs.get("reset_token_expires", None)
    user.oauth_id = kwargs.get("oauth_id", None)
    return user


# ---------------------------------------------------------------------------
# Email Verification — SVC-EXT-001 through SVC-EXT-005
# ---------------------------------------------------------------------------

class TestVerifyEmail:
    """SVC-EXT-001 through SVC-EXT-005"""

    @pytest.fixture
    def valid_user(self):
        return _make_user(
            verification_token="abc123",
            verification_token_expires=datetime.now(timezone.utc) + timedelta(hours=12),
            is_verified=False,
        )

    @pytest.fixture
    def mock_user_repo(self, valid_user):
        repo = AsyncMock()
        repo.get_by_verification_token.return_value = valid_user
        repo.update.return_value = valid_user
        return repo

    @pytest.fixture
    def service(self, mock_user_repo):
        from app.services.auth_service import AuthService
        return AuthService(user_repo=mock_user_repo)

    @pytest.mark.anyio
    async def test_valid_token_sets_is_verified_true(  # SVC-EXT-001
        self, service, mock_user_repo, valid_user
    ) -> None:
        await service.verify_email(token="abc123")

        mock_user_repo.update.assert_called_once()
        call_kwargs = mock_user_repo.update.call_args.kwargs
        assert call_kwargs["is_verified"] is True

    @pytest.mark.anyio
    async def test_clears_token_fields_after_success(  # SVC-EXT-002
        self, service, mock_user_repo, valid_user
    ) -> None:
        await service.verify_email(token="abc123")

        call_kwargs = mock_user_repo.update.call_args.kwargs
        assert call_kwargs["verification_token"] is None
        assert call_kwargs["verification_token_expires"] is None

    @pytest.mark.anyio
    async def test_raises_400_for_unknown_token(  # SVC-EXT-003
        self, mock_user_repo
    ) -> None:
        mock_user_repo.get_by_verification_token.return_value = None
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.verify_email(token="nonexistent")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Invalid token"

    @pytest.mark.anyio
    async def test_raises_400_for_expired_token(  # SVC-EXT-004
        self, mock_user_repo
    ) -> None:
        expired_user = _make_user(
            verification_token="abc123",
            verification_token_expires=datetime.now(timezone.utc) - timedelta(hours=25),
            is_verified=False,
        )
        mock_user_repo.get_by_verification_token.return_value = expired_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.verify_email(token="abc123")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Token expired"

    @pytest.mark.anyio
    async def test_raises_400_if_already_verified(  # SVC-EXT-005
        self, mock_user_repo
    ) -> None:
        verified_user = _make_user(
            verification_token="abc123",
            is_verified=True,
        )
        mock_user_repo.get_by_verification_token.return_value = verified_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.verify_email(token="abc123")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Email already verified"


# ---------------------------------------------------------------------------
# Forgot Password — SVC-EXT-006 through SVC-EXT-009
# ---------------------------------------------------------------------------

class TestForgotPassword:
    """SVC-EXT-006 through SVC-EXT-009"""

    @pytest.fixture
    def local_user(self):
        return _make_user(
            email="user@example.com",
            auth_provider=AuthProvider.LOCAL,
            password_hash="$2b$12$existinghash",
        )

    @pytest.fixture
    def mock_user_repo(self, local_user):
        repo = AsyncMock()
        repo.get_by_email.return_value = local_user
        repo.update.return_value = local_user
        return repo

    @pytest.fixture
    def mock_email_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_email_service):
        from app.services.auth_service import AuthService
        svc = AuthService(user_repo=mock_user_repo)
        svc._email_service = mock_email_service
        return svc

    @pytest.mark.anyio
    async def test_generates_reset_token_for_local_user(  # SVC-EXT-006
        self, service, mock_user_repo, mock_email_service
    ) -> None:
        await service.forgot_password(email="user@example.com")

        mock_user_repo.update.assert_called_once()
        call_kwargs = mock_user_repo.update.call_args.kwargs
        # Token is 64-char hex (32 bytes)
        assert len(call_kwargs["reset_token"]) == 64
        assert all(c in "0123456789abcdef" for c in call_kwargs["reset_token"])
        # Expiry ~1h in the future
        expires = call_kwargs["reset_token_expires"]
        assert isinstance(expires, datetime)
        delta = expires - datetime.now(timezone.utc)
        assert timedelta(minutes=55) < delta < timedelta(minutes=65)
        # Email was sent
        mock_email_service.send_password_reset_email.assert_called_once()

    @pytest.mark.anyio
    async def test_returns_without_error_for_unknown_email(  # SVC-EXT-007
        self, mock_user_repo, mock_email_service
    ) -> None:
        mock_user_repo.get_by_email.return_value = None
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._email_service = mock_email_service

        result = await service.forgot_password(email="nobody@example.com")

        assert result is None
        mock_user_repo.update.assert_not_called()
        mock_email_service.send_password_reset_email.assert_not_called()

    @pytest.mark.anyio
    async def test_silently_skips_oauth_only_user(  # SVC-EXT-008
        self, mock_user_repo, mock_email_service
    ) -> None:
        oauth_user = _make_user(
            email="oauth@example.com",
            auth_provider=AuthProvider.GOOGLE,
            password_hash=None,
        )
        mock_user_repo.get_by_email.return_value = oauth_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._email_service = mock_email_service

        result = await service.forgot_password(email="oauth@example.com")

        assert result is None
        mock_user_repo.update.assert_not_called()
        mock_email_service.send_password_reset_email.assert_not_called()

    @pytest.mark.anyio
    async def test_email_lookup_is_case_insensitive(  # SVC-EXT-009
        self, service, mock_user_repo
    ) -> None:
        await service.forgot_password(email="USER@Example.COM")

        # Repository should receive lowercased/stripped email
        call_args = mock_user_repo.get_by_email.call_args
        called_email = call_args.args[0] if call_args.args else call_args.kwargs.get("email")
        assert called_email == called_email.lower().strip()


# ---------------------------------------------------------------------------
# Reset Password — SVC-EXT-010 through SVC-EXT-014
# ---------------------------------------------------------------------------

class TestResetPassword:
    """SVC-EXT-010 through SVC-EXT-014"""

    @pytest.fixture
    def user_with_reset_token(self):
        return _make_user(
            reset_token="resetabc",
            reset_token_expires=datetime.now(timezone.utc) + timedelta(minutes=30),
            refresh_token_hash="somehash",
            password_hash="$2b$12$oldhash",
        )

    @pytest.fixture
    def mock_user_repo(self, user_with_reset_token):
        repo = AsyncMock()
        repo.get_by_reset_token.return_value = user_with_reset_token
        repo.update.return_value = user_with_reset_token
        return repo

    @pytest.fixture
    def service(self, mock_user_repo):
        from app.services.auth_service import AuthService
        return AuthService(user_repo=mock_user_repo)

    @pytest.mark.anyio
    async def test_updates_password_hash_for_valid_token(  # SVC-EXT-010
        self, service, mock_user_repo
    ) -> None:
        await service.reset_password(token="resetabc", new_password="newpass123")

        call_kwargs = mock_user_repo.update.call_args.kwargs
        new_hash = call_kwargs["password_hash"]
        assert new_hash != "$2b$12$oldhash"
        # Verify the new hash matches the new password
        from app.core.security import verify_password
        assert verify_password("newpass123", new_hash) is True

    @pytest.mark.anyio
    async def test_clears_reset_token_fields(  # SVC-EXT-011
        self, service, mock_user_repo
    ) -> None:
        await service.reset_password(token="resetabc", new_password="newpass123")

        call_kwargs = mock_user_repo.update.call_args.kwargs
        assert call_kwargs["reset_token"] is None
        assert call_kwargs["reset_token_expires"] is None

    @pytest.mark.anyio
    async def test_invalidates_all_sessions(  # SVC-EXT-012
        self, service, mock_user_repo
    ) -> None:
        await service.reset_password(token="resetabc", new_password="newpass123")

        call_kwargs = mock_user_repo.update.call_args.kwargs
        assert call_kwargs["refresh_token_hash"] is None

    @pytest.mark.anyio
    async def test_raises_400_for_unknown_token(  # SVC-EXT-013
        self, mock_user_repo
    ) -> None:
        mock_user_repo.get_by_reset_token.return_value = None
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.reset_password(token="nonexistent", new_password="newpass123")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Invalid reset token"

    @pytest.mark.anyio
    async def test_raises_400_for_expired_token(  # SVC-EXT-014
        self, mock_user_repo
    ) -> None:
        expired_user = _make_user(
            reset_token="resetabc",
            reset_token_expires=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        mock_user_repo.get_by_reset_token.return_value = expired_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.reset_password(token="resetabc", new_password="newpass123")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Reset link has expired"


# ---------------------------------------------------------------------------
# Google OAuth — SVC-EXT-015 through SVC-EXT-019
# ---------------------------------------------------------------------------

GOOGLE_USERINFO = {
    "email": "new@gmail.com",
    "name": "New User",
    "id": "google123",
    "picture": "https://lh3.googleusercontent.com/photo",
}


class TestGoogleOAuthCallback:
    """SVC-EXT-015 through SVC-EXT-019"""

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_oauth_id.return_value = None
        repo.get_by_email.return_value = None
        created_user = _make_user(
            email="new@gmail.com",
            auth_provider=AuthProvider.GOOGLE,
            oauth_id="google123",
            is_verified=True,
        )
        repo.create.return_value = created_user
        repo.update.return_value = created_user
        return repo

    @pytest.fixture
    def service(self, mock_user_repo):
        from app.services.auth_service import AuthService
        return AuthService(user_repo=mock_user_repo)

    def _patch_google_exchange(self, userinfo=None):
        """Return a context-manager that mocks the Google token+userinfo calls."""
        info = userinfo or GOOGLE_USERINFO

        async def _mock_exchange(code):
            return info

        return patch.object(
            # Patch the method that exchanges code for user info on the service
            # This will be something like auth_service._exchange_google_code
            # Since we don't know the exact method name yet, we patch httpx
            __name__,  # placeholder — tests import inside
        )

    @pytest.mark.anyio
    async def test_creates_new_user_on_first_login(  # SVC-EXT-015
        self, service, mock_user_repo
    ) -> None:
        # Mock the Google API interaction at the service level
        service._exchange_google_code = AsyncMock(return_value=GOOGLE_USERINFO)

        result = await service.google_oauth_callback(code="valid_code")

        # User created with correct fields
        mock_user_repo.create.assert_called_once()
        create_kwargs = mock_user_repo.create.call_args.kwargs
        assert create_kwargs["email"] == "new@gmail.com"
        assert create_kwargs["auth_provider"] == "GOOGLE"
        assert create_kwargs["oauth_id"] == "google123"
        assert create_kwargs["is_verified"] is True
        assert create_kwargs["password_hash"] is None
        assert create_kwargs["avatar_url"] == "https://lh3.googleusercontent.com/photo"

        # Returns tokens
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

        # Refresh token hash persisted
        mock_user_repo.update.assert_called()
        update_kwargs = mock_user_repo.update.call_args.kwargs
        assert "refresh_token_hash" in update_kwargs
        from app.core.security import hash_refresh_token
        assert update_kwargs["refresh_token_hash"] == hash_refresh_token(result.refresh_token)

    @pytest.mark.anyio
    async def test_logs_in_existing_oauth_user(  # SVC-EXT-016
        self, mock_user_repo
    ) -> None:
        existing_user = _make_user(
            email="existing@gmail.com",
            auth_provider=AuthProvider.GOOGLE,
            oauth_id="google123",
        )
        mock_user_repo.get_by_oauth_id.return_value = existing_user
        mock_user_repo.update.return_value = existing_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._exchange_google_code = AsyncMock(return_value=GOOGLE_USERINFO)

        result = await service.google_oauth_callback(code="valid_code")

        # No new user created
        mock_user_repo.create.assert_not_called()
        # Updated with last_login_at and refresh_token_hash
        mock_user_repo.update.assert_called()
        update_kwargs = mock_user_repo.update.call_args.kwargs
        assert "last_login_at" in update_kwargs
        assert "refresh_token_hash" in update_kwargs
        # Returns tokens
        assert result.access_token
        assert result.refresh_token

    @pytest.mark.anyio
    async def test_raises_400_when_email_exists_as_local_user(  # SVC-EXT-017
        self, mock_user_repo
    ) -> None:
        local_user = _make_user(
            email="new@gmail.com",
            auth_provider=AuthProvider.LOCAL,
        )
        mock_user_repo.get_by_oauth_id.return_value = None
        mock_user_repo.get_by_email.return_value = local_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._exchange_google_code = AsyncMock(return_value=GOOGLE_USERINFO)

        with pytest.raises(HTTPException) as exc:
            await service.google_oauth_callback(code="valid_code")
        assert exc.value.status_code == 400
        assert "Account exists with email/password" in exc.value.detail

    @pytest.mark.anyio
    async def test_raises_400_for_invalid_auth_code(  # SVC-EXT-018
        self, mock_user_repo
    ) -> None:
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._exchange_google_code = AsyncMock(side_effect=Exception("invalid_grant"))

        with pytest.raises(HTTPException) as exc:
            await service.google_oauth_callback(code="invalid_code")
        assert exc.value.status_code == 400
        assert exc.value.detail == "OAuth authentication failed"

    @pytest.mark.anyio
    async def test_raises_400_when_google_profile_has_no_email(  # SVC-EXT-019
        self, mock_user_repo
    ) -> None:
        no_email_info = {"name": "No Email", "id": "google456", "picture": "https://..."}

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._exchange_google_code = AsyncMock(return_value=no_email_info)

        with pytest.raises(HTTPException) as exc:
            await service.google_oauth_callback(code="valid_code")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Email not provided by Google"


# ---------------------------------------------------------------------------
# Registration Update — SVC-EXT-020, SVC-EXT-021
# ---------------------------------------------------------------------------

class TestRegisterWithVerification:
    """SVC-EXT-020, SVC-EXT-021"""

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()
        return repo

    @pytest.fixture
    def mock_email_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_email_service):
        from app.services.auth_service import AuthService
        svc = AuthService(user_repo=mock_user_repo)
        svc._email_service = mock_email_service
        return svc

    @pytest.mark.anyio
    async def test_register_generates_verification_token_and_sends_email(  # SVC-EXT-020
        self, service, mock_user_repo, mock_email_service
    ) -> None:
        await service.register(
            email="new@example.com",
            password="pass1234",
            full_name="New User",
        )

        # Token passed to create
        create_kwargs = mock_user_repo.create.call_args.kwargs
        token = create_kwargs["verification_token"]
        assert len(token) == 64
        assert all(c in "0123456789abcdef" for c in token)
        # Expiry ~24h in the future
        expires = create_kwargs["verification_token_expires"]
        assert isinstance(expires, datetime)
        delta = expires - datetime.now(timezone.utc)
        assert timedelta(hours=23) < delta < timedelta(hours=25)
        # Email sent
        mock_email_service.send_verification_email.assert_called_once()

    @pytest.mark.anyio
    async def test_register_succeeds_even_if_email_sending_fails(  # SVC-EXT-021
        self, mock_user_repo
    ) -> None:
        failing_email = AsyncMock()
        failing_email.send_verification_email.side_effect = Exception("SMTP failure")

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)
        service._email_service = failing_email

        # Should NOT raise — returns UserResponse
        result = await service.register(
            email="new@example.com",
            password="pass1234",
            full_name="New User",
        )
        assert result is not None


# ---------------------------------------------------------------------------
# Email Service — SVC-EXT-022, SVC-EXT-023
# ---------------------------------------------------------------------------

class TestEmailService:
    """SVC-EXT-022, SVC-EXT-023"""

    @pytest.mark.anyio
    async def test_send_verification_email_calls_smtp(  # SVC-EXT-022
        self,
    ) -> None:
        from app.services.email_service import EmailService

        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            service = EmailService()
            await service.send_verification_email(
                to_email="user@example.com",
                token="abc123",
                full_name="Test User",
            )

            mock_smtp.sendmail.assert_called_once()
            _, to_addr, msg_str = mock_smtp.sendmail.call_args.args
            assert to_addr == "user@example.com"
            assert "abc123" in msg_str

    @pytest.mark.anyio
    async def test_send_password_reset_email_calls_smtp(  # SVC-EXT-023
        self,
    ) -> None:
        from app.services.email_service import EmailService

        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            service = EmailService()
            await service.send_password_reset_email(
                to_email="user@example.com",
                token="reset123",
                full_name="Test User",
            )

            mock_smtp.sendmail.assert_called_once()
            _, to_addr, msg_str = mock_smtp.sendmail.call_args.args
            assert to_addr == "user@example.com"
            assert "reset123" in msg_str
