"""
Unit tests for app.services.auth_service — auth business logic with mocked repository.

All tests use real security functions (security.py must exist) but mock the DB repo.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import AuthProvider, UserRole


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

def _make_user(**kwargs):
    """Build a mock User object with sensible defaults using real enum values."""
    user = MagicMock()
    user.id = kwargs.get("id", uuid.uuid4())
    user.email = kwargs.get("email", "test@example.com")
    user.full_name = kwargs.get("full_name", "Test User")
    user.password_hash = kwargs.get("password_hash", "$2b$12$hashedpassword")
    user.is_active = kwargs.get("is_active", True)
    user.is_verified = kwargs.get("is_verified", False)
    # Use actual enums so service comparisons work correctly
    user.auth_provider = kwargs.get("auth_provider", AuthProvider.LOCAL)
    user.role = kwargs.get("role", UserRole.USER)
    user.refresh_token_hash = kwargs.get("refresh_token_hash", None)
    user.avatar_url = kwargs.get("avatar_url", None)
    user.last_login_at = kwargs.get("last_login_at", None)
    user.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    return user


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestAuthServiceRegister:
    """SVC-AUTH-001, SVC-AUTH-002"""

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_email.return_value = None  # no existing user
        repo.create.return_value = _make_user()
        return repo

    @pytest.fixture
    def service(self, mock_user_repo):
        from app.services.auth_service import AuthService
        return AuthService(user_repo=mock_user_repo)

    @pytest.mark.anyio
    async def test_register_creates_user_with_hashed_password(  # SVC-AUTH-001
        self, service, mock_user_repo
    ) -> None:
        await service.register(
            email="test@example.com",
            password="password123",
            full_name="Test User",
        )
        mock_user_repo.create.assert_called_once()
        call_kwargs = mock_user_repo.create.call_args.kwargs
        assert call_kwargs["password_hash"] != "password123"
        assert len(call_kwargs["password_hash"]) > 50  # bcrypt hash

    @pytest.mark.anyio
    async def test_register_raises_409_on_duplicate_email(  # SVC-AUTH-002
        self, mock_user_repo
    ) -> None:
        mock_user_repo.get_by_email.return_value = _make_user()  # email taken
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.register(
                email="existing@example.com",
                password="password123",
                full_name="Test",
            )
        assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestAuthServiceLogin:
    """SVC-AUTH-003 through SVC-AUTH-007"""

    @pytest.fixture
    def valid_user(self):
        from app.core.security import hash_password
        return _make_user(
            email="test@example.com",
            password_hash=hash_password("password123"),
            is_active=True,
            auth_provider=AuthProvider.LOCAL,
        )

    @pytest.fixture
    def mock_user_repo(self, valid_user):
        repo = AsyncMock()
        repo.get_by_email.return_value = valid_user
        repo.update.return_value = valid_user
        return repo

    @pytest.fixture
    def service(self, mock_user_repo):
        from app.services.auth_service import AuthService
        return AuthService(user_repo=mock_user_repo)

    @pytest.mark.anyio
    async def test_login_returns_tokens_and_saves_hash(  # SVC-AUTH-003
        self, service, mock_user_repo
    ) -> None:
        result = await service.login(
            email="test@example.com", password="password123"
        )
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        # refresh_token_hash must be persisted
        mock_user_repo.update.assert_called_once()
        update_kwargs = mock_user_repo.update.call_args.kwargs
        assert "refresh_token_hash" in update_kwargs
        assert update_kwargs["refresh_token_hash"] is not None

    @pytest.mark.anyio
    async def test_login_raises_401_on_wrong_password(  # SVC-AUTH-004
        self, service
    ) -> None:
        with pytest.raises(HTTPException) as exc:
            await service.login(email="test@example.com", password="wrongpassword")
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid credentials"

    @pytest.mark.anyio
    async def test_login_raises_401_if_user_not_found(  # SVC-AUTH-005
        self, mock_user_repo
    ) -> None:
        mock_user_repo.get_by_email.return_value = None
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.login(email="nobody@example.com", password="any")
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid credentials"

    @pytest.mark.anyio
    async def test_login_raises_403_if_user_blocked(  # SVC-AUTH-006
        self, mock_user_repo
    ) -> None:
        blocked_user = _make_user(is_active=False)
        from app.core.security import hash_password
        blocked_user.password_hash = hash_password("password123")
        mock_user_repo.get_by_email.return_value = blocked_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.login(email="blocked@example.com", password="password123")
        assert exc.value.status_code == 403
        assert "blocked" in exc.value.detail.lower()

    @pytest.mark.anyio
    async def test_login_raises_400_for_oauth_user(  # SVC-AUTH-007
        self, mock_user_repo
    ) -> None:
        oauth_user = _make_user(auth_provider=AuthProvider.GOOGLE, password_hash=None)
        mock_user_repo.get_by_email.return_value = oauth_user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.login(email="oauth@example.com", password="any")
        assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------

class TestAuthServiceRefresh:
    """SVC-AUTH-008, SVC-AUTH-009"""

    @pytest.fixture
    def user_with_hash(self):
        from app.core.security import create_refresh_token, hash_refresh_token
        # Must use a valid UUID as user_id — service calls uuid.UUID() on sub claim
        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        token = create_refresh_token(user_id=str(user_uuid))
        user = _make_user(id=user_uuid)
        user.refresh_token_hash = hash_refresh_token(token)
        return user, token

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.update.return_value = MagicMock()
        return repo

    @pytest.mark.anyio
    async def test_refresh_returns_new_tokens(  # SVC-AUTH-008
        self, user_with_hash, mock_user_repo
    ) -> None:
        user, token = user_with_hash
        mock_user_repo.get_by_id.return_value = user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        result = await service.refresh_tokens(refresh_token=token)
        assert result.access_token
        assert result.refresh_token
        # New hash must be persisted
        mock_user_repo.update.assert_called_once()

    @pytest.mark.anyio
    async def test_refresh_raises_401_on_hash_mismatch(  # SVC-AUTH-009
        self, mock_user_repo
    ) -> None:
        from app.core.security import create_refresh_token

        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000002")
        old_token = create_refresh_token(user_id=str(user_uuid))
        # User has a DIFFERENT hash — simulates token already rotated
        user = _make_user(id=user_uuid)
        user.refresh_token_hash = "a" * 64  # wrong hash, right length
        mock_user_repo.get_by_id.return_value = user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_user_repo)

        with pytest.raises(HTTPException) as exc:
            await service.refresh_tokens(refresh_token=old_token)
        assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    """SVC-AUTH-010"""

    @pytest.mark.anyio
    async def test_returns_user_for_valid_token(self) -> None:  # SVC-AUTH-010
        from app.core.security import create_access_token

        user = _make_user()
        # role.value gives "user" — the actual stored JWT string
        token = create_access_token(user_id=str(user.id), role=user.role.value)

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = user

        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_repo)

        result = await service.get_current_user(token=token)
        assert result == user

    @pytest.mark.anyio
    async def test_raises_401_for_invalid_token(self) -> None:
        mock_repo = AsyncMock()
        from app.services.auth_service import AuthService
        service = AuthService(user_repo=mock_repo)

        with pytest.raises(HTTPException) as exc:
            await service.get_current_user(token="invalid.token")
        assert exc.value.status_code == 401
