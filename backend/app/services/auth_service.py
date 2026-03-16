"""
Botlixio — Authentication service.

Business logic for register, login, token refresh, and current-user resolution.
All database access goes through UserRepository.
"""

import uuid
from datetime import datetime

from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.enums import AuthProvider
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    # ── Register ──────────────────────────────────────────────────────────

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
    ) -> UserResponse:
        """
        Create a new LOCAL user account.

        Raises:
            HTTPException(409) — email already registered
        """
        existing = await self._repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = await self._repo.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            auth_provider="LOCAL",
            is_verified=False,
        )
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
            last_login_at=datetime.utcnow(),
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
