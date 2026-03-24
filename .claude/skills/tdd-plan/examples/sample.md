# Example output — extracted from auth-extended spec

This is a real excerpt showing the expected format and level of detail.

---

## Summary

| Layer | Count | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Unit  | 3     | 1  | 2  | 0   |
| Service | 20  | 12 | 6  | 2   |
| API   | 14    | 8  | 4  | 2   |
| **Total** | **37** | **21** | **12** | **4** |

---

## Unit Tests

### UNIT-EXT-001: generate_token returns 64-char hex string
- **Priority**: P1
- **Preconditions**: `generate_token` function exists in `app/core/security.py`
- **Steps**:
  1. Call `generate_token()`
  2. Check return value length and hex validity
- **Expected**: Returns a 64-character string where all characters are valid hex digits (0-9, a-f)

### UNIT-EXT-003: generate_token is cryptographically random
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Verify `generate_token` uses `secrets.token_hex` (not `random`)
- **Expected**: Implementation uses `secrets` module (source inspection or mock verification)

---

## Service Tests — Email Verification

### SVC-EXT-001: verify_email with valid token sets is_verified=true
- **Priority**: P0
- **Preconditions**: User exists with `verification_token="abc123"`, `verification_token_expires` in the future, `is_verified=False`
- **Steps**:
  1. Call `auth_service.verify_email(token="abc123")`
- **Expected**: `user_repo.update` called with `is_verified=True`, `verification_token=None`, `verification_token_expires=None`

### SVC-EXT-006: register still succeeds if email sending fails
- **Priority**: P0
- **Preconditions**: `email_service.send_verification_email` raises an exception
- **Steps**:
  1. Call `auth_service.register(email="new@example.com", password="pass1234", full_name="New User")`
- **Expected**: Returns `UserResponse` without raising — email failure is logged but does not block registration

---

## API Tests

### API-EXT-005: POST /forgot-password with unknown email returns 200 (same response)
- **Priority**: P0
- **Preconditions**: No user with the email
- **Steps**:
  1. `POST /api/v1/auth/forgot-password { "email": "nobody@example.com" }`
- **Expected**: 200 with identical response body as API-EXT-004 — no email enumeration
