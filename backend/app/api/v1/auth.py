"""
Botlixio — Authentication routes.

Public endpoints: register, login, refresh, verify-email, forgot-password,
                  reset-password, google, google/callback
Protected endpoints: GET /me
"""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
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


# ── Verify Email ──────────────────────────────────────────────────────────────


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    body: VerifyEmailRequest,
    service: AuthService = Depends(_get_auth_service),
) -> MessageResponse:
    """Verify a user's email via one-time token."""
    await service.verify_email(token=body.token)
    return MessageResponse(message="Email verified successfully")


# ── Forgot Password ──────────────────────────────────────────────────────────


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    body: ForgotPasswordRequest,
    service: AuthService = Depends(_get_auth_service),
) -> MessageResponse:
    """Initiate password reset. Always returns 200 (no email enumeration)."""
    await service.forgot_password(email=body.email)
    return MessageResponse(message="If that email exists, a reset link has been sent")


# ── Reset Password ────────────────────────────────────────────────────────────


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest,
    service: AuthService = Depends(_get_auth_service),
) -> MessageResponse:
    """Reset password using a one-time reset token."""
    await service.reset_password(token=body.token, new_password=body.new_password)
    return MessageResponse(message="Password reset successfully")


# ── Google OAuth ──────────────────────────────────────────────────────────────


@router.get("/google", status_code=status.HTTP_302_FOUND)
async def google_oauth_redirect():
    """Redirect to Google OAuth consent screen."""
    settings = get_settings()
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    })
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
        status_code=302,
    )


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = "",
    service: AuthService = Depends(_get_auth_service),
):
    """Handle Google OAuth callback — exchange code, create/login user, redirect."""
    if not code:
        raise __import__("fastapi").HTTPException(
            status_code=400, detail="Missing authorization code"
        )

    tokens = await service.google_oauth_callback(code=code)

    settings = get_settings()
    params = urlencode({
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
    })
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?{params}",
        status_code=302,
    )
