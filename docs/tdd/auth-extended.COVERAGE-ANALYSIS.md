# Coverage Analysis: Authentication Extended

Spec: `docs/specs/auth-extended.SPEC.md`
Test Cases: `docs/tdd/auth-extended.TEST-CASES.md`

---

## Summary

| Category | Total | Covered | Weakly Covered | Uncovered |
|----------|-------|---------|----------------|-----------|
| Happy Flows | 22 | 22 | 0 | 0 |
| Edge Cases | 12 | 12 | 0 | 0 |
| API Contracts | 13 | 13 | 0 | 0 |
| Business Rules | 5 | 5 | 0 | 0 |
| **Total** | **52** | **52** | **0** | **0** |

**Coverage score**: 100% fully covered · 0% weakly covered · 0% uncovered

> **Update**: All gaps from initial analysis have been addressed — see Recommendations (Resolved) below.

---

## Spec Requirements Index

### Email Verification Flow
- `SPEC-VERIFY-001`: Find user by `verification_token` (exact match) → **Covered** by SVC-EXT-001, SVC-EXT-003
- `SPEC-VERIFY-002`: Check `verification_token_expires` is in the future → **Covered** by SVC-EXT-004
- `SPEC-VERIFY-003`: Set `is_verified=True` → **Covered** by SVC-EXT-001, API-EXT-001
- `SPEC-VERIFY-004`: Clear `verification_token=None`, `verification_token_expires=None` → **Covered** by SVC-EXT-002, API-EXT-001
- `SPEC-VERIFY-005`: Return 200 with `"Email verified successfully"` → **Covered** by API-EXT-001
- `SPEC-VERIFY-006`: Return 400 `"Invalid token"` for unknown token → **Covered** by SVC-EXT-003, API-EXT-002
- `SPEC-VERIFY-007`: Return 400 `"Token expired"` for expired token → **Covered** by SVC-EXT-004, API-EXT-003
- `SPEC-VERIFY-008`: Return 400 `"Email already verified"` if already verified → **Covered** by SVC-EXT-005, API-EXT-004

### Forgot Password Flow
- `SPEC-FORGOT-001`: Find user by email (case-insensitive) → **Covered** by SVC-EXT-009
- `SPEC-FORGOT-002`: If user not found, still return 200 → **Covered** by SVC-EXT-007, API-EXT-006
- `SPEC-FORGOT-003`: Generate 32-byte hex `reset_token` → **Covered** by SVC-EXT-006
- `SPEC-FORGOT-004`: Set `reset_token_expires = now + 1h` → **Covered** by SVC-EXT-006, API-EXT-005
- `SPEC-FORGOT-005`: Send reset email via EmailService → **Covered** by SVC-EXT-006
- `SPEC-FORGOT-006`: Return 200 with `"If that email exists, a reset link has been sent"` → **Covered** by API-EXT-005, API-EXT-006
- `SPEC-FORGOT-007`: Silently skip OAuth-only users (no email sent) → **Covered** by SVC-EXT-008

### Reset Password Flow
- `SPEC-RESET-001`: Find user by `reset_token` (exact match) → **Covered** by SVC-EXT-010, SVC-EXT-013
- `SPEC-RESET-002`: Return 400 `"Invalid reset token"` for unknown token → **Covered** by SVC-EXT-013, API-EXT-009
- `SPEC-RESET-003`: Return 400 `"Reset link has expired"` for expired token → **Covered** by SVC-EXT-014, API-EXT-010
- `SPEC-RESET-004`: Hash new_password with bcrypt → **Covered** by SVC-EXT-010
- `SPEC-RESET-005`: Update `password_hash` → **Covered** by SVC-EXT-010, API-EXT-008
- `SPEC-RESET-006`: Clear `reset_token=None`, `reset_token_expires=None` → **Covered** by SVC-EXT-011, API-EXT-008
- `SPEC-RESET-007`: Clear `refresh_token_hash=None` (invalidate sessions) → **Covered** by SVC-EXT-012, API-EXT-008
- `SPEC-RESET-008`: Return 200 with `"Password reset successfully"` → **Covered** by API-EXT-008

### Google OAuth Flow
- `SPEC-OAUTH-001`: `GET /auth/google` returns 302 redirect to Google consent URL → **Covered** by API-EXT-012
- `SPEC-OAUTH-002`: Consent URL includes `client_id`, `redirect_uri`, `scope=openid email profile` → **Covered** by API-EXT-012
- `SPEC-OAUTH-003`: Exchange auth code for access token via Google token endpoint → **Covered** by SVC-EXT-015 (implicitly via mock setup)
- `SPEC-OAUTH-004`: Fetch user info (email, name, picture, id) from Google → **Covered** by SVC-EXT-015 (implicitly via mock setup)
- `SPEC-OAUTH-005`: Lookup user by `oauth_id` + `auth_provider=GOOGLE` → **Covered** by SVC-EXT-015, SVC-EXT-016
- `SPEC-OAUTH-006`: Existing OAuth user — update `last_login_at`, issue tokens → **Covered** by SVC-EXT-016, API-EXT-014
- `SPEC-OAUTH-007`: New user — email exists as LOCAL → return 400 → **Covered** by SVC-EXT-017, API-EXT-015
- `SPEC-OAUTH-008`: New user — email not found → create with `GOOGLE`, `is_verified=True`, `password_hash=None` → **Covered** by SVC-EXT-015, API-EXT-013
- `SPEC-OAUTH-009`: Issue tokens, store refresh hash → **Covered** by SVC-EXT-015 (strengthened to assert `refresh_token_hash` persisted)
- `SPEC-OAUTH-010`: Redirect to `{FRONTEND_URL}/auth/callback?access_token=...&refresh_token=...` → **Covered** by API-EXT-013
- `SPEC-OAUTH-011`: Invalid auth code → 400 "OAuth authentication failed" → **Covered** by SVC-EXT-018, API-EXT-016
- `SPEC-OAUTH-012`: Missing email in Google profile → 400 → **Covered** by SVC-EXT-019

### Registration Update
- `SPEC-REG-001`: Generate `verification_token = secrets.token_hex(32)` → **Covered** by SVC-EXT-020
- `SPEC-REG-002`: Set `verification_token_expires = now + 24h` → **Covered** by SVC-EXT-020
- `SPEC-REG-003`: Pass token to `UserRepository.create()` → **Covered** by SVC-EXT-020
- `SPEC-REG-004`: Send verification email via EmailService → **Covered** by SVC-EXT-020
- `SPEC-REG-005`: Registration succeeds if email sending fails → **Covered** by SVC-EXT-021

### Business Rules
- `SPEC-BIZ-001`: No email enumeration — forgot-password always returns 200 → **Covered** by SVC-EXT-007, API-EXT-006
- `SPEC-BIZ-002`: Verification tokens valid 24h → **Covered** by SVC-EXT-004, API-EXT-003
- `SPEC-BIZ-003`: Reset tokens valid 1h → **Covered** by SVC-EXT-014, API-EXT-010
- `SPEC-BIZ-004`: OAuth users created with `is_verified=True` → **Covered** by SVC-EXT-015
- `SPEC-BIZ-005`: Endpoints registered under existing `/auth` router → **Covered** by API-EXT-017

### Schema Definitions
- `SPEC-SCHEMA-001`: `MessageResponse` schema added with `message: str` field → **Covered** implicitly by API tests checking response bodies

---

## Uncovered Requirements

All previously uncovered requirements have been addressed. See Recommendations (Resolved) below.

---

## Weakly Covered Requirements

All previously weak test cases have been strengthened. See Recommendations (Resolved) below.

---

## Orphaned Tests

### UNIT-EXT-001: generate_token returns 64-char hex string
- **Maps to**: No explicit spec requirement — spec says "Generate 32-byte hex `reset_token` via `secrets.token_hex(32)`" but doesn't specify a standalone `generate_token` function
- **Assessment**: **Keep** — covers an implicit requirement. If a utility function is created for token generation, this test validates its output format. If `secrets.token_hex(32)` is called inline, this test should be removed or converted to a service-level assertion.

### UNIT-EXT-002: generate_token produces unique values
- **Maps to**: Same as UNIT-EXT-001
- **Assessment**: **Keep** — validates cryptographic randomness. Same caveat about inline vs utility function.

### API-EXT-007: POST /forgot-password with invalid email format returns 422
- **Maps to**: No explicit spec requirement (Pydantic framework default)
- **Assessment**: **Keep** — the spec's API contract table explicitly lists `422 | Invalid email format` so it's implicitly required.

### API-EXT-011: POST /reset-password with short password returns 422
- **Maps to**: Edge case table row "Reset password — password too short (<8) | 422"
- **Assessment**: **Keep** — explicitly listed in the spec's edge cases table.

---

## Recommendations (Resolved)

1. **SVC-EXT-015 strengthened** (Critical — resolved): Added assertion that `user_repo.update` is called with `refresh_token_hash` matching `hash_refresh_token(returned_refresh_token)` after OAuth user creation.

2. **API-EXT-018 added** (High — resolved): New test verifies `POST /forgot-password` response times are consistent for known vs unknown emails, preventing timing-based enumeration.

3. **API-EXT-017 added** (Medium — resolved): New structural test verifies all 5 Phase 3 endpoints are registered on the `/auth` router.

4. **Clarify UNIT-EXT-001/002 target** (Low — open): The spec doesn't define a standalone `generate_token` function. During implementation, if tokens are generated inline via `secrets.token_hex(32)`, convert these unit tests to service-level assertions within SVC-EXT-006 and SVC-EXT-020 instead.
