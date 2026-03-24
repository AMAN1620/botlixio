# Spec: Authentication

**Phase**: 2 (Core) + 3 (Extended)
**Routes**: `/api/v1/auth/*`
**Access**: Public (register, login, verify, forgot/reset password, OAuth) | User (me, refresh)

**Files** (Phase 2 — Core):
- `app/core/security.py` — password hashing + JWT logic
- `app/schemas/auth.py` — Pydantic request/response schemas
- `app/repositories/user_repo.py` — User DB queries
- `app/services/auth_service.py` — Auth business logic
- `app/api/v1/auth.py` — Route handlers
- `app/api/deps.py` — `get_current_user` FastAPI dependency

**Files** (Phase 3 — Extended):
- `app/services/email_service.py` — Resend email integration

---

## Overview

Botlixio uses JWT-based authentication with email/password (bcrypt) and Google OAuth. Access tokens expire in 30 minutes; refresh tokens in 7 days with rotation on each use. Email verification is required to create agents but not to log in. Password reset uses time-limited tokens (1h). All auth endpoints that could leak user existence always return 200 (no email enumeration).

---

## User Stories

| ID | As a... | I want to... | So that... |
|----|---------|-------------|-----------|
| US-01 | Visitor | Register with email & password | I can access the platform |
| US-02 | Visitor | Log in with email & password | I get a JWT to access protected routes |
| US-03 | User | Refresh my access token | I stay logged in without re-entering credentials |
| US-04 | User | Verify my email | I can create agents |
| US-05 | User | Reset my forgotten password | I can regain access to my account |
| US-06 | Developer | Access `GET /me` with a valid JWT | I can retrieve the current user's profile |
| US-07 | Visitor | Log in via Google OAuth | I can sign in without a password |

---

## Happy Flows

### Registration Flow
1. Client sends `POST /api/v1/auth/register` with `{ email, password, full_name }`
2. Backend validates: email format, password ≥8 chars, email not taken
3. Hash password with bcrypt (cost 12)
4. Generate 32-byte hex `verification_token`
5. Create `User` with `is_verified=False`, `auth_provider=LOCAL`
6. Send verification email via Resend (Phase 3)
7. Return `201` with `UserResponse`

### Login Flow
1. Client sends `POST /api/v1/auth/login` with `{ email, password }`
2. Find user by email → lookup is case-insensitive
3. Verify bcrypt password hash
4. Check `is_active=True`
5. Create JWT access token (30min) + refresh token (7 days)
6. Update `last_login_at`
7. Return `200` with `TokenResponse { access_token, refresh_token, token_type: "bearer" }`

### Token Refresh Flow
1. Client sends `POST /api/v1/auth/refresh` with `{ refresh_token }`
2. Decode and verify JWT signature + expiry
3. Compute `SHA-256(refresh_token)` and compare to `user.refresh_token_hash` in DB
4. If hash mismatch → `401` (token already rotated or revoked)
5. Load user from DB, verify `is_active=True`
6. Issue **new** access token + **new** refresh token
7. Update `user.refresh_token_hash = SHA-256(new_refresh_token)` in DB
8. Return `200` with new `TokenResponse`

> ⚠️ **Why DB storage?** JWTs are stateless — without persisting a hash, the server has no way to invalidate an old refresh token. The old token would remain valid for its full 7-day TTL even after rotation.

### Get Current User Flow
1. Client sends `GET /api/v1/auth/me` with `Authorization: Bearer <token>`
2. `get_current_user` dependency decodes token, loads User from DB
3. Return `200` with `UserResponse`

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Duplicate email on register | `409 Conflict` — `"Email already registered"` |
| Login — email not found | `401 Unauthorized` — generic `"Invalid credentials"` (no email enumeration) |
| Login — wrong password | `401 Unauthorized` — generic `"Invalid credentials"` |
| Login — `is_active=False` | `403 Forbidden` — `"Account has been blocked"` |
| Login — OAuth user tries password login | `400 Bad Request` — `"Please use {provider} to sign in"` |
| `GET /me` — expired token | `401 Unauthorized` — `"Token has expired"` |
| `GET /me` — invalid token | `401 Unauthorized` — `"Invalid token"` |
| `GET /me` — user deleted mid-session | `401 Unauthorized` — `"User not found"` |
| Refresh — expired refresh token | `401 Unauthorized` |
| Refresh — invalid JWT signature | `401 Unauthorized` |
| Refresh — expired JWT (7d) | `401 Unauthorized` |
| Refresh — token already rotated (reuse of old token) | `401 Unauthorized` — hash mismatch detected |
| Email verification — valid token | `200` — `is_verified=True` |
| Email verification — expired token (24h) | `400 Bad Request` — `"Token expired"` |
| Email verification — invalid token | `400 Bad Request` — `"Invalid token"` |
| Forgot password — email not found | `200` — always (no enumeration) |
| Reset password — expired token (1h) | `400 Bad Request` — `"Reset link has expired"` |
| Reset password — invalid token | `400 Bad Request` — `"Invalid reset token"` |

---

## Pydantic Schemas

```python
# app/schemas/auth.py

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import UserRole, AuthProvider


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


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


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
```

---

## API Contract

### `POST /api/v1/auth/register`
- **Auth**: Public
- **Body**: `RegisterRequest`
- **Response 201**: `{ "data": UserResponse }`
- **Response 409**: `{ "detail": "Email already registered" }`

### `POST /api/v1/auth/login`
- **Auth**: Public
- **Body**: `LoginRequest`
- **Response 200**: `TokenResponse`
- **Response 401**: `{ "detail": "Invalid credentials" }`
- **Response 403**: `{ "detail": "Account has been blocked" }`

### `POST /api/v1/auth/refresh`
- **Auth**: Public (refresh token in body)
- **Body**: `RefreshRequest`
- **Response 200**: `TokenResponse`
- **Response 401**: `{ "detail": "Invalid or expired refresh token" }`

### `GET /api/v1/auth/me`
- **Auth**: Bearer JWT
- **Response 200**: `{ "data": UserResponse }`
- **Response 401**: `{ "detail": "Token has expired" | "Invalid token" }`

### `POST /api/v1/auth/verify-email` *(Phase 3)*
- **Auth**: Public
- **Body**: `VerifyEmailRequest`
- **Response 200**: `{ "message": "Email verified successfully" }`
- **Response 400**: `{ "detail": "Token expired" | "Invalid token" }`

### `POST /api/v1/auth/forgot-password` *(Phase 3)*
- **Auth**: Public
- **Body**: `ForgotPasswordRequest`
- **Response 200**: `{ "message": "If that email exists, a reset link has been sent" }` *(always)*

### `POST /api/v1/auth/reset-password` *(Phase 3)*
- **Auth**: Public
- **Body**: `ResetPasswordRequest`
- **Response 200**: `{ "message": "Password reset successfully" }`
- **Response 400**: `{ "detail": "Reset link has expired" | "Invalid reset token" }`

---

## Security Functions (`app/core/security.py`)

```python
def hash_password(password: str) -> str:
    """Hash with bcrypt, cost 12."""

def verify_password(plain: str, hashed: str) -> bool:
    """Verify bcrypt hash. Returns True/False."""

def create_access_token(user_id: str, role: str) -> str:
    """JWT: exp=30min, payload={sub, role, type='access', jti=uuid}"""

def create_refresh_token(user_id: str) -> str:
    """JWT: exp=7 days, payload={sub, type='refresh', jti=uuid}"""

def decode_token(token: str) -> dict:
    """Decode + verify JWT. Raises HTTP 401 on invalid/expired."""

def hash_refresh_token(token: str) -> str:
    """SHA-256 hash of a refresh token string → stored in users.refresh_token_hash.
    Never store the raw token. Only the hash goes in the DB.
    """
```

### Refresh Token Rotation — How it works

```
POST /login:
  token = create_refresh_token(user_id)
  user.refresh_token_hash = hash_refresh_token(token)  ← save to DB
  return token to client

POST /refresh:
  decode JWT → get user_id
  if hash_refresh_token(incoming_token) != user.refresh_token_hash:
      raise 401  ← old/reused/stolen token detected
  new_token = create_refresh_token(user_id)
  user.refresh_token_hash = hash_refresh_token(new_token)  ← rotate in DB
  return new_token

POST /logout (future):
  user.refresh_token_hash = None  ← immediate revocation
```

---

## Test Scenarios

### Unit (pure functions — `tests/unit/test_security.py`)
- `hash_password` returns a hash different from input
- `verify_password` returns True for correct password
- `verify_password` returns False for wrong password
- `create_access_token` returns a decodable JWT with correct `sub` and `role`
- `create_refresh_token` returns a JWT with `type='refresh'`
- `decode_token` raises 401 on expired token
- `decode_token` raises 401 on tampered token

### Unit (schemas — `tests/unit/test_auth_schemas.py`)
- `RegisterRequest` rejects password < 8 chars
- `RegisterRequest` rejects invalid email format
- `RegisterRequest` rejects empty full_name
- `LoginRequest` rejects empty password

### Service (mocked repo — `tests/unit/test_auth_service.py`)
- `register` creates a user with hashed password
- `register` raises 409 on duplicate email
- `login` returns tokens + saves refresh token hash to DB
- `login` returns tokens on valid credentials
- `login` raises 401 on wrong password
- `login` raises 401 if user not found
- `login` raises 403 if `is_active=False`
- `refresh` issues new tokens and updates `refresh_token_hash` in DB
- `refresh` raises 401 when incoming hash doesn't match DB (token reuse detected)
- `get_current_user` returns user for valid token
- `get_current_user` raises 401 for invalid/expired token

### API (httpx — `tests/integration/test_auth_api.py`)
- `POST /register` → 201, returns user data
- `POST /register` → 409 on duplicate email
- `POST /register` → 422 on missing fields
- `POST /login` → 200, returns tokens
- `POST /login` → 401 on wrong password
- `POST /login` → 401 on unknown email
- `GET /me` → 200 with valid token
- `GET /me` → 401 with no token
- `GET /me` → 401 with expired token
- `POST /refresh` → 200, returns new tokens
- `POST /refresh` → 401 with invalid token

---

## Acceptance Criteria

- [ ] `POST /register` creates a user with bcrypt-hashed password
- [ ] `POST /login` returns valid JWT access + refresh tokens
- [ ] `GET /me` returns user data when token is valid
- [ ] `GET /me` returns 401 when token is missing or expired
- [ ] Duplicate email registration returns 409
- [ ] Wrong password returns 401 with generic message (no email hint)
- [ ] Blocked account returns 403
- [ ] `POST /refresh` issues new token pair
- [ ] `get_current_user` dependency works on any protected route
- [ ] All unit tests and integration tests pass

---

## Deferred to Phase 3

- Email verification (`POST /verify-email`)
- Password forgot/reset (`POST /forgot-password`, `POST /reset-password`)
- Google + GitHub OAuth (full callback flow, account-linking — see feature doc)
- Resend email integration (`app/services/email_service.py`)

**Verification token expiry — enforcement (Phase 3):**
```
On register:
  user.verification_token = secrets.token_hex(32)
  user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)

On POST /verify-email:
  if datetime.utcnow() > user.verification_token_expires → 400 "Token expired"
  if user.verification_token != token → 400 "Invalid token"
  user.is_verified = True
  user.verification_token = None          ← clear on use
  user.verification_token_expires = None  ← clear on use
```
Note: `verification_token_expires` column is already in the DB (migration `73f0ec838292`).
