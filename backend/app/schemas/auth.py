"""
Botlixio — Pydantic schemas for Authentication.

Request schemas:  RegisterRequest, LoginRequest, RefreshRequest
Response schemas: TokenResponse, UserResponse
Phase 3 schemas:  VerifyEmailRequest, ForgotPasswordRequest, ResetPasswordRequest
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import AuthProvider, UserRole


# ── Request schemas ──────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Phase 3 request schemas (defined here, endpoints added in Phase 3) ───────


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    """Generic success message for non-data responses."""
    message: str


# ── Response schemas ─────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    auth_provider: AuthProvider
    avatar_url: str | None
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}
