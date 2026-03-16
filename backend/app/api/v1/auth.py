"""
Botlixio — Authentication routes.

Public endpoints: register, login, refresh
Protected endpoints: GET /me
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Build an AuthService with a scoped DB session."""
    return AuthService(user_repo=UserRepository(db))


# ── Register ─────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
) -> dict:
    """Create a new user account. Returns the created user profile."""
    user = await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return {"data": user.model_dump()}


# ── Login ─────────────────────────────────────────────────────────────────────


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """Authenticate with email + password. Returns JWT access + refresh tokens."""
    return await service.login(email=body.email, password=body.password)


# ── Refresh ───────────────────────────────────────────────────────────────────


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    body: RefreshRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """Rotate refresh token. Returns new access + refresh token pair."""
    return await service.refresh_tokens(refresh_token=body.refresh_token)


# ── Me (protected) ────────────────────────────────────────────────────────────


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the currently authenticated user's profile."""
    return {"data": UserResponse.model_validate(current_user).model_dump()}
