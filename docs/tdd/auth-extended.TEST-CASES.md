# Test Cases: Authentication Extended — Phase 3

Generated from `docs/specs/auth-extended.SPEC.md`

---

## Summary

| Layer | Count | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Unit  | 2     | 1  | 1  | 0   |
| Service | 21 | 14 | 5  | 2   |
| API   | 18    | 11 | 5  | 2   |
| **Total** | **41** | **26** | **11** | **4** |

---

## Unit Tests

### UNIT-EXT-001: generate_token returns 64-char hex string
- **Priority**: P1
- **Preconditions**: A token generation utility exists (e.g., wrapping `secrets.token_hex(32)`)
- **Steps**:
  1. Call the token generation function
  2. Check return value length and hex validity
- **Expected**: Returns a 64-character string where all characters are valid hex digits (0-9, a-f)

### UNIT-EXT-002: generate_token produces unique values
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Call the token generation function twice
  2. Compare the two results
- **Expected**: The two tokens are different (cryptographic randomness via `secrets` module)

---

## Service Tests — Email Verification

### SVC-EXT-001: verify_email with valid token sets is_verified=True
- **Priority**: P0
- **Preconditions**: User exists with `verification_token="abc123"`, `verification_token_expires` in the future, `is_verified=False`. Mock `user_repo.get_by_verification_token` returns this user.
- **Steps**:
  1. Call `auth_service.verify_email(token="abc123")`
- **Expected**: `user_repo.update` called with `is_verified=True`, `verification_token=None`, `verification_token_expires=None`

### SVC-EXT-002: verify_email clears token fields after success
- **Priority**: P0
- **Preconditions**: Same as SVC-EXT-001
- **Steps**:
  1. Call `auth_service.verify_email(token="abc123")`
- **Expected**: `user_repo.update` called with `verification_token=None` AND `verification_token_expires=None` — token is single-use

### SVC-EXT-003: verify_email raises 400 for unknown token
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_verification_token` returns `None`
- **Steps**:
  1. Call `auth_service.verify_email(token="nonexistent")`
- **Expected**: Raises `HTTPException(400)` with detail `"Invalid token"`

### SVC-EXT-004: verify_email raises 400 for expired token
- **Priority**: P0
- **Preconditions**: User exists with `verification_token="abc123"`, `verification_token_expires` set to 25 hours ago, `is_verified=False`
- **Steps**:
  1. Call `auth_service.verify_email(token="abc123")`
- **Expected**: Raises `HTTPException(400)` with detail `"Token expired"`

### SVC-EXT-005: verify_email raises 400 if user already verified
- **Priority**: P0
- **Preconditions**: User exists with `verification_token="abc123"`, `is_verified=True`
- **Steps**:
  1. Call `auth_service.verify_email(token="abc123")`
- **Expected**: Raises `HTTPException(400)` with detail `"Email already verified"`

---

## Service Tests — Forgot Password

### SVC-EXT-006: forgot_password generates reset token for existing LOCAL user
- **Priority**: P0
- **Preconditions**: LOCAL user exists with email `"user@example.com"`. Mock `user_repo.get_by_email` returns this user. Mock `email_service.send_password_reset_email`.
- **Steps**:
  1. Call `auth_service.forgot_password(email="user@example.com")`
- **Expected**: `user_repo.update` called with a 64-char hex `reset_token` and `reset_token_expires` ~1 hour in the future. `email_service.send_password_reset_email` called with the user's email and generated token.

### SVC-EXT-007: forgot_password returns without error for unknown email
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns `None`
- **Steps**:
  1. Call `auth_service.forgot_password(email="nobody@example.com")`
- **Expected**: Returns `None` without raising. No calls to `user_repo.update` or `email_service`.

### SVC-EXT-008: forgot_password silently skips OAuth-only user
- **Priority**: P0
- **Preconditions**: User exists with `auth_provider=GOOGLE`, `password_hash=None`. Mock `user_repo.get_by_email` returns this user.
- **Steps**:
  1. Call `auth_service.forgot_password(email="oauth@example.com")`
- **Expected**: Returns `None` without raising. `email_service.send_password_reset_email` NOT called. No reset token generated.

### SVC-EXT-009: forgot_password email lookup is case-insensitive
- **Priority**: P1
- **Preconditions**: User exists with email `"user@example.com"`. Mock `user_repo.get_by_email`.
- **Steps**:
  1. Call `auth_service.forgot_password(email="USER@Example.COM")`
- **Expected**: `user_repo.get_by_email` called with lowercased/stripped email

---

## Service Tests — Reset Password

### SVC-EXT-010: reset_password updates password hash for valid token
- **Priority**: P0
- **Preconditions**: User exists with `reset_token="resetabc"`, `reset_token_expires` in the future. Mock `user_repo.get_by_reset_token` returns this user.
- **Steps**:
  1. Call `auth_service.reset_password(token="resetabc", new_password="newpass123")`
- **Expected**: `user_repo.update` called with a new bcrypt `password_hash` (different from the old one). `verify_password("newpass123", new_hash)` returns True.

### SVC-EXT-011: reset_password clears reset token fields
- **Priority**: P0
- **Preconditions**: Same as SVC-EXT-010
- **Steps**:
  1. Call `auth_service.reset_password(token="resetabc", new_password="newpass123")`
- **Expected**: `user_repo.update` called with `reset_token=None`, `reset_token_expires=None`

### SVC-EXT-012: reset_password invalidates all sessions
- **Priority**: P0
- **Preconditions**: Same as SVC-EXT-010. User has `refresh_token_hash="somehash"`.
- **Steps**:
  1. Call `auth_service.reset_password(token="resetabc", new_password="newpass123")`
- **Expected**: `user_repo.update` called with `refresh_token_hash=None` — all existing sessions are invalidated

### SVC-EXT-013: reset_password raises 400 for unknown token
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_reset_token` returns `None`
- **Steps**:
  1. Call `auth_service.reset_password(token="nonexistent", new_password="newpass123")`
- **Expected**: Raises `HTTPException(400)` with detail `"Invalid reset token"`

### SVC-EXT-014: reset_password raises 400 for expired token
- **Priority**: P0
- **Preconditions**: User exists with `reset_token="resetabc"`, `reset_token_expires` set to 2 hours ago
- **Steps**:
  1. Call `auth_service.reset_password(token="resetabc", new_password="newpass123")`
- **Expected**: Raises `HTTPException(400)` with detail `"Reset link has expired"`

---

## Service Tests — Google OAuth

### SVC-EXT-015: google_oauth_callback creates new user on first login
- **Priority**: P0
- **Preconditions**: Mock Google token exchange returns valid access token. Mock Google userinfo returns `{email: "new@gmail.com", name: "New User", id: "google123", picture: "https://..."}`. Mock `user_repo.get_by_oauth_id` returns `None`. Mock `user_repo.get_by_email` returns `None`.
- **Steps**:
  1. Call `auth_service.google_oauth_callback(code="valid_code")`
- **Expected**: `user_repo.create` called with `email="new@gmail.com"`, `auth_provider="GOOGLE"`, `oauth_id="google123"`, `is_verified=True`, `password_hash=None`, `avatar_url="https://..."`. Returns `TokenResponse` with valid access and refresh tokens. `user_repo.update` called with `refresh_token_hash` matching `hash_refresh_token(returned_refresh_token)` — refresh token hash must be persisted for token rotation to work.

### SVC-EXT-016: google_oauth_callback logs in existing OAuth user
- **Priority**: P0
- **Preconditions**: Existing GOOGLE user with `oauth_id="google123"`. Mock `user_repo.get_by_oauth_id` returns this user.
- **Steps**:
  1. Call `auth_service.google_oauth_callback(code="valid_code")`
- **Expected**: No new user created. `user_repo.update` called with updated `last_login_at` and `refresh_token_hash`. Returns `TokenResponse`.

### SVC-EXT-017: google_oauth_callback raises 400 when email exists as LOCAL user
- **Priority**: P0
- **Preconditions**: LOCAL user exists with same email. Mock `user_repo.get_by_oauth_id` returns `None`. Mock `user_repo.get_by_email` returns the LOCAL user.
- **Steps**:
  1. Call `auth_service.google_oauth_callback(code="valid_code")`
- **Expected**: Raises `HTTPException(400)` with detail `"Account exists with email/password"`

### SVC-EXT-018: google_oauth_callback raises 400 for invalid auth code
- **Priority**: P1
- **Preconditions**: Mock Google token exchange raises error or returns error response
- **Steps**:
  1. Call `auth_service.google_oauth_callback(code="invalid_code")`
- **Expected**: Raises `HTTPException(400)` with detail `"OAuth authentication failed"`

### SVC-EXT-019: google_oauth_callback raises 400 when Google profile has no email
- **Priority**: P1
- **Preconditions**: Mock Google token exchange succeeds. Mock Google userinfo returns profile without `email` field.
- **Steps**:
  1. Call `auth_service.google_oauth_callback(code="valid_code")`
- **Expected**: Raises `HTTPException(400)` with detail `"Email not provided by Google"`

---

## Service Tests — Registration Update

### SVC-EXT-020: register generates verification token and sends email
- **Priority**: P1
- **Preconditions**: Mock `user_repo.get_by_email` returns `None` (no existing user). Mock `email_service.send_verification_email`.
- **Steps**:
  1. Call `auth_service.register(email="new@example.com", password="pass1234", full_name="New User")`
- **Expected**: `user_repo.create` called with a 64-char hex `verification_token` and `verification_token_expires` ~24h in the future. `email_service.send_verification_email` called with the user's email and token.

### SVC-EXT-021: register succeeds even if email sending fails
- **Priority**: P1
- **Preconditions**: `email_service.send_verification_email` raises an exception
- **Steps**:
  1. Call `auth_service.register(email="new@example.com", password="pass1234", full_name="New User")`
- **Expected**: Returns `UserResponse` without raising — email failure is logged but does not block registration

---

## Service Tests — Email Service

### SVC-EXT-022: send_verification_email calls Resend API with correct payload
- **Priority**: P2
- **Preconditions**: Mock httpx client
- **Steps**:
  1. Call `email_service.send_verification_email(to_email="user@example.com", token="abc123", full_name="Test User")`
- **Expected**: HTTP POST to `https://api.resend.com/emails` with Authorization header containing API key, `to` containing the email, `html` containing the verification link with token

### SVC-EXT-023: send_password_reset_email calls Resend API with correct payload
- **Priority**: P2
- **Preconditions**: Mock httpx client
- **Steps**:
  1. Call `email_service.send_password_reset_email(to_email="user@example.com", token="reset123", full_name="Test User")`
- **Expected**: HTTP POST to `https://api.resend.com/emails` with `html` containing the reset link with token

---

## API Tests — Email Verification

### API-EXT-001: POST /verify-email with valid token returns 200
- **Priority**: P0
- **Preconditions**: User in DB with `verification_token="validtoken"`, `verification_token_expires` in the future, `is_verified=False`
- **Steps**:
  1. `POST /api/v1/auth/verify-email` with `{ "token": "validtoken" }`
- **Expected**: `200` with `{ "message": "Email verified successfully" }`. User in DB now has `is_verified=True`, `verification_token=None`.

### API-EXT-002: POST /verify-email with unknown token returns 400
- **Priority**: P0
- **Preconditions**: No user with this verification token
- **Steps**:
  1. `POST /api/v1/auth/verify-email` with `{ "token": "nonexistent" }`
- **Expected**: `400` with `{ "detail": "Invalid token" }`

### API-EXT-003: POST /verify-email with expired token returns 400
- **Priority**: P0
- **Preconditions**: User with `verification_token="expiredtoken"`, `verification_token_expires` 25 hours ago
- **Steps**:
  1. `POST /api/v1/auth/verify-email` with `{ "token": "expiredtoken" }`
- **Expected**: `400` with `{ "detail": "Token expired" }`

### API-EXT-004: POST /verify-email for already verified user returns 400
- **Priority**: P1
- **Preconditions**: User with `verification_token="validtoken"`, `is_verified=True`
- **Steps**:
  1. `POST /api/v1/auth/verify-email` with `{ "token": "validtoken" }`
- **Expected**: `400` with `{ "detail": "Email already verified" }`

---

## API Tests — Forgot Password

### API-EXT-005: POST /forgot-password with existing email returns 200
- **Priority**: P0
- **Preconditions**: LOCAL user exists with email `"user@example.com"`. Mock email service.
- **Steps**:
  1. `POST /api/v1/auth/forgot-password` with `{ "email": "user@example.com" }`
- **Expected**: `200` with `{ "message": "If that email exists, a reset link has been sent" }`. User in DB has `reset_token` set and `reset_token_expires` ~1h in the future.

### API-EXT-006: POST /forgot-password with unknown email returns 200 (no enumeration)
- **Priority**: P0
- **Preconditions**: No user with this email
- **Steps**:
  1. `POST /api/v1/auth/forgot-password` with `{ "email": "nobody@example.com" }`
- **Expected**: `200` with identical response body as API-EXT-005. No DB changes. No email sent.

### API-EXT-007: POST /forgot-password with invalid email format returns 422
- **Priority**: P2
- **Preconditions**: None
- **Steps**:
  1. `POST /api/v1/auth/forgot-password` with `{ "email": "not-an-email" }`
- **Expected**: `422` Pydantic validation error

---

## API Tests — Reset Password

### API-EXT-008: POST /reset-password with valid token updates password
- **Priority**: P0
- **Preconditions**: User with `reset_token="resettoken"`, `reset_token_expires` in the future
- **Steps**:
  1. `POST /api/v1/auth/reset-password` with `{ "token": "resettoken", "new_password": "newsecure123" }`
- **Expected**: `200` with `{ "message": "Password reset successfully" }`. User can now log in with `"newsecure123"`. Old password no longer works. `reset_token` cleared. `refresh_token_hash` cleared.

### API-EXT-009: POST /reset-password with unknown token returns 400
- **Priority**: P0
- **Preconditions**: No user with this reset token
- **Steps**:
  1. `POST /api/v1/auth/reset-password` with `{ "token": "badtoken", "new_password": "newsecure123" }`
- **Expected**: `400` with `{ "detail": "Invalid reset token" }`

### API-EXT-010: POST /reset-password with expired token returns 400
- **Priority**: P0
- **Preconditions**: User with `reset_token="expiredtoken"`, `reset_token_expires` 2 hours ago
- **Steps**:
  1. `POST /api/v1/auth/reset-password` with `{ "token": "expiredtoken", "new_password": "newsecure123" }`
- **Expected**: `400` with `{ "detail": "Reset link has expired" }`

### API-EXT-011: POST /reset-password with short password returns 422
- **Priority**: P2
- **Preconditions**: None
- **Steps**:
  1. `POST /api/v1/auth/reset-password` with `{ "token": "anytoken", "new_password": "short" }`
- **Expected**: `422` Pydantic validation error (password min_length=8)

---

## API Tests — Google OAuth

### API-EXT-012: GET /auth/google redirects to Google consent URL
- **Priority**: P1
- **Preconditions**: Google OAuth config set (`GOOGLE_CLIENT_ID`, `GOOGLE_REDIRECT_URI`)
- **Steps**:
  1. `GET /api/v1/auth/google` (follow_redirects=False)
- **Expected**: `302` redirect. Location header contains `accounts.google.com`, `client_id`, `redirect_uri`, `scope=openid email profile`

### API-EXT-013: GET /auth/google/callback with valid code creates user and redirects
- **Priority**: P0
- **Preconditions**: Mock Google token exchange and userinfo API. No existing user with the Google email.
- **Steps**:
  1. `GET /api/v1/auth/google/callback?code=valid_code` (follow_redirects=False)
- **Expected**: `302` redirect to `{FRONTEND_URL}/auth/callback` with `access_token` and `refresh_token` in query params. New user created in DB with `auth_provider=GOOGLE`, `is_verified=True`.

### API-EXT-014: GET /auth/google/callback with existing OAuth user logs in and redirects
- **Priority**: P1
- **Preconditions**: GOOGLE user already exists in DB with matching `oauth_id`. Mock Google APIs.
- **Steps**:
  1. `GET /api/v1/auth/google/callback?code=valid_code` (follow_redirects=False)
- **Expected**: `302` redirect with tokens. No new user created. `last_login_at` updated.

### API-EXT-015: GET /auth/google/callback with email conflict returns 400
- **Priority**: P0
- **Preconditions**: LOCAL user exists with same email as Google profile. Mock Google APIs.
- **Steps**:
  1. `GET /api/v1/auth/google/callback?code=valid_code`
- **Expected**: `400` with `{ "detail": "Account exists with email/password" }`

### API-EXT-016: GET /auth/google/callback with invalid code returns 400
- **Priority**: P1
- **Preconditions**: Mock Google token exchange to fail
- **Steps**:
  1. `GET /api/v1/auth/google/callback?code=bad_code`
- **Expected**: `400` with `{ "detail": "OAuth authentication failed" }`

---

## API Tests — Route Registration

### API-EXT-017: All Phase 3 auth endpoints are registered
- **Priority**: P1
- **Preconditions**: FastAPI app is initialized
- **Steps**:
  1. Inspect `app.routes` or issue requests to each new endpoint
  2. Check for: `POST /api/v1/auth/verify-email`, `POST /api/v1/auth/forgot-password`, `POST /api/v1/auth/reset-password`, `GET /api/v1/auth/google`, `GET /api/v1/auth/google/callback`
- **Expected**: All 5 routes exist on the app. Requests to these paths do NOT return `404` (may return 400/422 for missing body, but not 404).

---

## API Tests — Anti-Enumeration Timing

### API-EXT-018: POST /forgot-password response time is consistent for known vs unknown emails
- **Priority**: P0
- **Preconditions**: LOCAL user exists with email `"known@example.com"`. No user with email `"unknown@example.com"`. Mock email service (so actual sending doesn't skew timing).
- **Steps**:
  1. `POST /api/v1/auth/forgot-password` with `{ "email": "known@example.com" }` — record response time
  2. `POST /api/v1/auth/forgot-password` with `{ "email": "unknown@example.com" }` — record response time
  3. Compare response times
- **Expected**: Both requests return `200` with identical response body. Response times are within a reasonable delta (e.g., <200ms difference) — the unknown-email path must not be noticeably faster than the known-email path, to prevent timing-based email enumeration.
