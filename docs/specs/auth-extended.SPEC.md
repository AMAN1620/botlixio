# Spec: Authentication — Extended

**Mode**: Proactive
**Phase**: 3
**Routes**: `POST /api/v1/auth/verify-email`, `POST /api/v1/auth/forgot-password`, `POST /api/v1/auth/reset-password`, `GET /api/v1/auth/google`, `GET /api/v1/auth/google/callback`
**Access**: Public

**Files** (existing — will be extended):
- `app/api/v1/auth.py` — route handlers (add 5 endpoints)
- `app/services/auth_service.py` — business logic (add 4 methods)
- `app/schemas/auth.py` — schemas (add `MessageResponse`)
- `app/repositories/user_repo.py` — data access (add 3 query methods)

**Files** (new):
- `app/services/email_service.py` — Resend email integration

**Depends on**: Phase 2 (Core Auth) — fully implemented.

---

## Overview

Phase 3 extends the core auth module with email verification, password reset, and Google OAuth. Email verification uses a 24h one-time token generated at registration. Password reset uses a 1h one-time token. Google OAuth creates verified accounts on first login. All endpoints that could leak user existence return 200 regardless (no email enumeration).

---

## User Stories

| ID | As a... | I want to... | So that... |
|----|---------|-------------|-----------|
| US-04 | User | Verify my email via a link | I can create agents |
| US-05 | User | Reset my forgotten password | I can regain access to my account |
| US-07 | Visitor | Log in via Google OAuth | I can sign in without a password |

---

## Happy Flows

### Email Verification Flow
1. User receives verification email (sent during registration) with link: `{FRONTEND_URL}/verify-email?token={token}`
2. Frontend extracts token, sends `POST /api/v1/auth/verify-email` with `{ token }`
3. Backend finds user by `verification_token` (exact match)
4. Backend checks `verification_token_expires` — must be in the future
5. Set `user.is_verified = True`
6. Clear `user.verification_token = None`, `user.verification_token_expires = None`
7. Return `200` with `{ "message": "Email verified successfully" }`

### Forgot Password Flow
1. Client sends `POST /api/v1/auth/forgot-password` with `{ email }`
2. Backend finds user by email (case-insensitive)
3. If user not found -> **still return 200** (no email enumeration)
4. If user found:
   a. Generate 32-byte hex `reset_token` via `secrets.token_hex(32)`
   b. Set `user.reset_token = reset_token`
   c. Set `user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)`
   d. Send password reset email via EmailService with link: `{FRONTEND_URL}/reset-password?token={reset_token}`
5. Return `200` with `{ "message": "If that email exists, a reset link has been sent" }`

### Reset Password Flow
1. Client sends `POST /api/v1/auth/reset-password` with `{ token, new_password }`
2. Backend finds user by `reset_token` (exact match)
3. If no user found -> `400` "Invalid reset token"
4. If `datetime.utcnow() > user.reset_token_expires` -> `400` "Reset link has expired"
5. Hash `new_password` with bcrypt
6. Update `user.password_hash = hashed_password`
7. Clear `user.reset_token = None`, `user.reset_token_expires = None`
8. Clear `user.refresh_token_hash = None` (invalidate all active sessions)
9. Return `200` with `{ "message": "Password reset successfully" }`

### Google OAuth Flow
1. Client navigates to `GET /api/v1/auth/google`
2. Backend builds Google OAuth consent URL with `client_id`, `redirect_uri`, `scope=openid email profile`
3. Backend returns `302` redirect to Google consent URL
4. User authorizes -> Google redirects to `GET /api/v1/auth/google/callback?code={auth_code}`
5. Backend exchanges `code` for access token via Google token endpoint (`https://oauth2.googleapis.com/token`)
6. Backend fetches user info from `https://www.googleapis.com/oauth2/v2/userinfo` (email, name, picture, id)
7. Lookup user by `oauth_id=google_id` AND `auth_provider=GOOGLE`:
   a. **Found** -> update `last_login_at`, issue tokens
   b. **Not found** -> lookup by email:
      - Email exists with `auth_provider=LOCAL` -> `400` "Account exists with email/password. Please log in and link Google in settings."
      - Email not found -> create new User: `auth_provider=GOOGLE`, `oauth_id=google_id`, `is_verified=True`, `password_hash=None`, `avatar_url=picture`
8. Issue access + refresh tokens, store refresh hash in DB
9. Redirect to `{FRONTEND_URL}/auth/callback?access_token={token}&refresh_token={token}`

### Registration Update (Phase 3 enhancement to existing flow)
The existing `register` method in `AuthService` will be updated to:
1. Generate `verification_token = secrets.token_hex(32)`
2. Set `verification_token_expires = datetime.utcnow() + timedelta(hours=24)`
3. Pass both to `UserRepository.create()` (already accepts these params)
4. Send verification email via `EmailService.send_verification_email()`

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Email verification — valid token | `200` — `is_verified=True`, token cleared |
| Email verification — expired token (24h) | `400 Bad Request` — `"Token expired"` |
| Email verification — invalid/unknown token | `400 Bad Request` — `"Invalid token"` |
| Email verification — already verified user | `400 Bad Request` — `"Email already verified"` |
| Forgot password — email not found | `200` — always (no enumeration) |
| Forgot password — OAuth-only user (no password) | `200` — silently skip (no email sent) |
| Reset password — expired token (1h) | `400 Bad Request` — `"Reset link has expired"` |
| Reset password — invalid/unknown token | `400 Bad Request` — `"Invalid reset token"` |
| Reset password — password too short (<8) | `422` — Pydantic validation error |
| OAuth callback — invalid auth code | `400 Bad Request` — `"OAuth authentication failed"` |
| OAuth callback — email exists as LOCAL user | `400 Bad Request` — `"Account exists with email/password"` |
| OAuth callback — missing email in Google profile | `400 Bad Request` — `"Email not provided by Google"` |

---

## Pydantic Schemas

Existing schemas in `app/schemas/auth.py` (verbatim — already defined):

```python
class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
```

New schema to add:

```python
class MessageResponse(BaseModel):
    """Generic success message for non-data responses."""
    message: str
```

---

## API Contract

### `POST /api/v1/auth/verify-email`
- **Auth**: Public
- **Body**: `VerifyEmailRequest`
- **Responses**:

| Code | Condition | Body |
|------|-----------|------|
| 200 | Token valid, email verified | `{ "message": "Email verified successfully" }` |
| 400 | Token not found | `{ "detail": "Invalid token" }` |
| 400 | Token expired (24h) | `{ "detail": "Token expired" }` |
| 400 | User already verified | `{ "detail": "Email already verified" }` |
| 422 | Missing token field | Pydantic validation error |

### `POST /api/v1/auth/forgot-password`
- **Auth**: Public
- **Body**: `ForgotPasswordRequest`
- **Responses**:

| Code | Condition | Body |
|------|-----------|------|
| 200 | Always (email found or not) | `{ "message": "If that email exists, a reset link has been sent" }` |
| 422 | Invalid email format | Pydantic validation error |

### `POST /api/v1/auth/reset-password`
- **Auth**: Public
- **Body**: `ResetPasswordRequest`
- **Responses**:

| Code | Condition | Body |
|------|-----------|------|
| 200 | Token valid, password updated | `{ "message": "Password reset successfully" }` |
| 400 | Token not found | `{ "detail": "Invalid reset token" }` |
| 400 | Token expired (1h) | `{ "detail": "Reset link has expired" }` |
| 422 | Password < 8 chars | Pydantic validation error |

### `GET /api/v1/auth/google`
- **Auth**: Public
- **Responses**:

| Code | Condition | Body |
|------|-----------|------|
| 302 | Redirect to Google | Redirect to Google OAuth consent URL |

### `GET /api/v1/auth/google/callback`
- **Auth**: Public (Google redirects here)
- **Query params**: `code` (authorization code)
- **Responses**:

| Code | Condition | Body |
|------|-----------|------|
| 302 | Success | Redirect to `{FRONTEND_URL}/auth/callback?access_token=...&refresh_token=...` |
| 400 | Invalid code | `{ "detail": "OAuth authentication failed" }` |
| 400 | Email exists as LOCAL user | `{ "detail": "Account exists with email/password" }` |

---

## Service Layer — New Methods (`app/services/auth_service.py`)

Add to existing `AuthService` class:

```python
async def verify_email(self, *, token: str) -> None:
    """
    Verify a user's email address using a one-time token.

    1. Find user by verification_token via repo
    2. Check already verified -> 400
    3. Check token expiry (24h) -> 400
    4. Set is_verified=True, clear token fields

    Raises:
        HTTPException(400) — invalid token, expired token, already verified
    """

async def forgot_password(self, *, email: str) -> None:
    """
    Initiate password reset — generate token, send email.

    Always succeeds (no exception) regardless of whether email exists.

    1. Lookup user by email
    2. If not found or OAuth-only user: no-op
    3. If found: generate reset_token (32-byte hex), set expiry = now + 1h
    4. Send reset email via EmailService
    """

async def reset_password(self, *, token: str, new_password: str) -> None:
    """
    Reset password using a one-time reset token.

    1. Find user by reset_token via repo
    2. Check token expiry (1h) -> 400
    3. Hash new password, update password_hash
    4. Clear reset_token, reset_token_expires, refresh_token_hash

    Raises:
        HTTPException(400) — invalid token, expired token
    """

async def google_oauth_callback(self, *, code: str) -> TokenResponse:
    """
    Handle Google OAuth callback.

    1. Exchange auth code for Google access token (httpx)
    2. Fetch user info from Google
    3. Find or create user
    4. Issue JWT tokens

    Raises:
        HTTPException(400) — invalid code, email conflict
    """
```

### Registration Update

The existing `register` method will be updated to:
- Accept an `EmailService` dependency (or receive it via constructor)
- Generate `verification_token` and `verification_token_expires`
- Call `email_service.send_verification_email()` after user creation

---

## Repository Layer — New Methods (`app/repositories/user_repo.py`)

Add to existing `UserRepository` class:

```python
async def get_by_verification_token(self, token: str) -> User | None:
    """Find user by verification_token. Returns None if not found."""
    result = await self._db.execute(
        select(User).where(User.verification_token == token)
    )
    return result.scalar_one_or_none()

async def get_by_reset_token(self, token: str) -> User | None:
    """Find user by reset_token. Returns None if not found."""
    result = await self._db.execute(
        select(User).where(User.reset_token == token)
    )
    return result.scalar_one_or_none()

async def get_by_oauth_id(self, oauth_id: str, provider: AuthProvider) -> User | None:
    """Find user by oauth_id + auth_provider. Returns None if not found."""
    result = await self._db.execute(
        select(User).where(
            User.oauth_id == oauth_id,
            User.auth_provider == provider,
        )
    )
    return result.scalar_one_or_none()
```

---

## Email Service (`app/services/email_service.py` — new file)

```python
import httpx
from app.core.config import get_settings


class EmailService:
    """Send transactional emails via Resend API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.RESEND_API_KEY
        self._from_email = settings.FROM_EMAIL
        self._frontend_url = settings.FRONTEND_URL

    async def send_verification_email(
        self, *, to_email: str, token: str, full_name: str
    ) -> None:
        """
        Send email verification link.
        Link: {FRONTEND_URL}/verify-email?token={token}
        """

    async def send_password_reset_email(
        self, *, to_email: str, token: str, full_name: str
    ) -> None:
        """
        Send password reset link. Expires in 1 hour.
        Link: {FRONTEND_URL}/reset-password?token={token}
        """
```

Resend API call pattern:
```python
async with httpx.AsyncClient() as client:
    await client.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {self._api_key}"},
        json={
            "from": self._from_email,
            "to": [to_email],
            "subject": "...",
            "html": "...",
        },
    )
```

---

## Config Additions (`app/core/config.py`)

New settings needed for Phase 3:

```python
# Email (Resend)
RESEND_API_KEY: str = ""
FROM_EMAIL: str = "noreply@botlix.io"

# OAuth (Google)
GOOGLE_CLIENT_ID: str = ""
GOOGLE_CLIENT_SECRET: str = ""
GOOGLE_REDIRECT_URI: str = ""  # {BACKEND_URL}/api/v1/auth/google/callback

# Frontend URL (for email links and OAuth redirects)
FRONTEND_URL: str = "http://localhost:3000"
```

---

## Database Columns Used

All columns already exist in the `users` table (migrations applied):

| Column | Type | Purpose |
|--------|------|---------|
| `verification_token` | `String(255), nullable` | One-time email verification token |
| `verification_token_expires` | `DateTime, nullable` | 24h expiry for verification token |
| `reset_token` | `String(255), nullable` | One-time password reset token |
| `reset_token_expires` | `DateTime, nullable` | 1h expiry for reset token |
| `oauth_id` | `String(255), nullable` | Google/GitHub user ID |
| `auth_provider` | `Enum(AuthProvider)` | `LOCAL`, `GOOGLE`, `GITHUB`, `APPLE` |
| `is_verified` | `Boolean, default=False` | Email verified flag |

No new migrations required.

---

## Acceptance Criteria

- [ ] `POST /verify-email` sets `is_verified=True` for valid, unexpired token
- [ ] `POST /verify-email` returns 400 for expired token (24h)
- [ ] `POST /verify-email` returns 400 for invalid/unknown token
- [ ] `POST /verify-email` returns 400 if user already verified
- [ ] `POST /verify-email` clears token fields after successful verification
- [ ] `POST /forgot-password` always returns 200 (no email enumeration)
- [ ] `POST /forgot-password` generates reset token with 1h expiry when user exists
- [ ] `POST /forgot-password` sends email via Resend when LOCAL user exists
- [ ] `POST /forgot-password` skips silently for OAuth-only users
- [ ] `POST /reset-password` updates password hash for valid token
- [ ] `POST /reset-password` invalidates all sessions (clears `refresh_token_hash`)
- [ ] `POST /reset-password` clears reset token fields after success
- [ ] `POST /reset-password` returns 400 for expired token (1h)
- [ ] `POST /reset-password` returns 400 for invalid/unknown token
- [ ] `GET /auth/google` redirects to Google consent URL with correct params
- [ ] `GET /auth/google/callback` creates new user on first OAuth login with `is_verified=True`
- [ ] `GET /auth/google/callback` logs in existing OAuth user and issues tokens
- [ ] `GET /auth/google/callback` returns 400 when email exists as LOCAL user
- [ ] Registration generates verification token and sends email via Resend
- [ ] `EmailService` is injectable and mockable for testing
- [ ] All new endpoints are registered under the existing `/auth` router
