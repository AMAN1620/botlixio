"""
Botlixio — Authentication service.

Business logic for register, login, token refresh, current-user resolution,
email verification, password reset, and Google OAuth.
All database access goes through UserRepository.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.enums import AuthProvider
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserResponse
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo
        self._email_service: EmailService | None = None

    def _get_email_service(self) -> EmailService:
        if self._email_service is None:
            self._email_service = EmailService()
        return self._email_service

    # ── Register ──────────────────────────────────────────────────────────

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
    ) -> UserResponse:
        """
        Create a new LOCAL user account with verification token.

        Raises:
            HTTPException(409) — email already registered
        """
        existing = await self._repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        verification_token = generate_token()
        verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        user = await self._repo.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            auth_provider="LOCAL",
            is_verified=False,
            verification_token=verification_token,
            verification_token_expires=verification_token_expires,
        )

        # Send verification email — failure must not block registration
        try:
            email_service = self._get_email_service()
            await email_service.send_verification_email(
                to_email=email,
                token=verification_token,
                full_name=full_name,
            )
        except Exception:
            logger.warning("Failed to send verification email to %s", email)

        return UserResponse.model_validate(user)

    # ── Login ────────────────────────────────────────────────────────────

    async def login(self, *, email: str, password: str) -> TokenResponse:
        """
        Authenticate a LOCAL user, issue tokens, persist hash.

        Raises:
            HTTPException(401) — user not found or wrong password
            HTTPException(403) — account blocked
            HTTPException(400) — OAuth user attempted password login
        """
        user = await self._repo.get_by_email(email)

        # User not found — same generic error as wrong password (no enumeration)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # OAuth-only account tried password login
        if user.auth_provider != AuthProvider.LOCAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please use {str(user.auth_provider)} to sign in",
            )

        # Blocked account — check AFTER provider check to avoid leaking info
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been blocked",
            )

        # Wrong password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Issue tokens
        access_token = create_access_token(
            user_id=str(user.id), role=user.role.value
        )
        refresh_token = create_refresh_token(user_id=str(user.id))

        # Persist refresh token hash + last login
        await self._repo.update(
            user,
            refresh_token_hash=hash_refresh_token(refresh_token),
            last_login_at=datetime.now(timezone.utc),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ── Refresh ───────────────────────────────────────────────────────────

    async def refresh_tokens(self, *, refresh_token: str) -> TokenResponse:
        """
        Rotate refresh tokens — verify hash match, issue new pair.

        Raises:
            HTTPException(401) — invalid/expired JWT or hash mismatch (token reuse)
        """
        payload = decode_token(refresh_token)  # raises 401 if expired/invalid

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        try:
            uid = uuid.UUID(user_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user = await self._repo.get_by_id(uid)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Verify hash matches — detects token reuse after rotation
        if user.refresh_token_hash != hash_refresh_token(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Rotate — issue new pair, update hash in DB
        new_access = create_access_token(user_id=str(user.id), role=user.role.value)
        new_refresh = create_refresh_token(user_id=str(user.id))

        await self._repo.update(
            user,
            refresh_token_hash=hash_refresh_token(new_refresh),
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
        )

    # ── Get current user ─────────────────────────────────────────────────

    async def get_current_user(self, *, token: str):
        """
        Resolve a User from a Bearer access token.

        Raises:
            HTTPException(401) — invalid/expired token or user not found
        """
        payload = decode_token(token)  # raises 401 if invalid

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        try:
            uid = uuid.UUID(user_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user = await self._repo.get_by_id(uid)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

    # ── Verify Email ─────────────────────────────────────────────────────

    async def verify_email(self, *, token: str) -> None:
        """
        Verify a user's email address using a one-time token.

        Raises:
            HTTPException(400) — invalid token, expired token, already verified
        """
        user = await self._repo.get_by_verification_token(token)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token",
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified",
            )

        if user.verification_token_expires and datetime.now(timezone.utc) > user.verification_token_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expired",
            )

        await self._repo.update(
            user,
            is_verified=True,
            verification_token=None,
            verification_token_expires=None,
        )

    # ── Forgot Password ──────────────────────────────────────────────────

    async def forgot_password(self, *, email: str) -> None:
        """
        Initiate password reset. Always succeeds (no email enumeration).
        """
        user = await self._repo.get_by_email(email.lower().strip())

        if user is None:
            return None

        # Skip OAuth-only users (no password to reset)
        if user.auth_provider != AuthProvider.LOCAL or user.password_hash is None:
            return None

        reset_token = generate_token()
        reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        await self._repo.update(
            user,
            reset_token=reset_token,
            reset_token_expires=reset_token_expires,
        )

        try:
            email_service = self._get_email_service()
            await email_service.send_password_reset_email(
                to_email=user.email,
                token=reset_token,
                full_name=user.full_name,
            )
        except Exception as e:
            logger.warning("Failed to send password reset email to %s: %s", user.email, e)

        return None

    # ── Reset Password ───────────────────────────────────────────────────

    async def reset_password(self, *, token: str, new_password: str) -> None:
        """
        Reset password using a one-time reset token.

        Raises:
            HTTPException(400) — invalid token, expired token
        """
        user = await self._repo.get_by_reset_token(token)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token",
            )

        if user.reset_token_expires and datetime.now(timezone.utc) > user.reset_token_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset link has expired",
            )

        await self._repo.update(
            user,
            password_hash=hash_password(new_password),
            reset_token=None,
            reset_token_expires=None,
            refresh_token_hash=None,
        )

    # ── Google OAuth ─────────────────────────────────────────────────────

    async def _exchange_google_code(self, code: str) -> dict:
        """Exchange a Google auth code for user info."""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_resp.json()
            if "access_token" not in token_data:
                raise Exception("Failed to exchange code for token")

            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            return userinfo_resp.json()

    async def google_oauth_callback(self, *, code: str) -> TokenResponse:
        """
        Handle Google OAuth callback.

        Raises:
            HTTPException(400) — invalid code, email conflict, missing email
        """
        try:
            userinfo = await self._exchange_google_code(code)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth authentication failed",
            )

        email = userinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google",
            )

        google_id = userinfo.get("id", "")
        name = userinfo.get("name", "")
        picture = userinfo.get("picture")

        # Check for existing OAuth user
        user = await self._repo.get_by_oauth_id(google_id, AuthProvider.GOOGLE)

        if user is None:
            # Check for email conflict with LOCAL user
            existing = await self._repo.get_by_email(email)
            if existing and existing.auth_provider == AuthProvider.LOCAL:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account exists with email/password",
                )

            # Create new OAuth user
            user = await self._repo.create(
                email=email,
                password_hash=None,
                full_name=name,
                auth_provider="GOOGLE",
                oauth_id=google_id,
                is_verified=True,
                avatar_url=picture,
            )

        # Issue tokens
        access_token = create_access_token(
            user_id=str(user.id), role=user.role.value
        )
        refresh_token = create_refresh_token(user_id=str(user.id))

        await self._repo.update(
            user,
            refresh_token_hash=hash_refresh_token(refresh_token),
            last_login_at=datetime.now(timezone.utc),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
