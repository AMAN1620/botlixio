# Test Cases: Authentication

Generated from: `backend/specs/auth.SPEC.md`
Generated on: 2026-03-15

## Summary

| Layer | Count | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Unit — Security | 7 | 5 | 2 | 0 |
| Unit — Schemas | 4 | 2 | 2 | 0 |
| Service | 10 | 7 | 3 | 0 |
| API | 11 | 7 | 4 | 0 |
| **Total** | **32** | **21** | **11** | **0** |

---

## Unit Tests — Security (`tests/unit/test_security.py`)

### UNIT-SEC-001: hash_password produces a hash distinct from input
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Call `hash_password("mypassword123")`
- **Expected**: Returns a string ≠ `"mypassword123"`, length > 50 (bcrypt format)

### UNIT-SEC-002: verify_password returns True for correct password
- **Priority**: P0
- **Preconditions**: A hashed password from `hash_password`
- **Steps**:
  1. Call `verify_password("mypassword123", hashed)`
- **Expected**: Returns `True`

### UNIT-SEC-003: verify_password returns False for wrong password
- **Priority**: P0
- **Preconditions**: A hashed password from `hash_password`
- **Steps**:
  1. Call `verify_password("wrongpassword", hashed)`
- **Expected**: Returns `False`

### UNIT-SEC-004: create_access_token returns a decodable JWT with correct claims
- **Priority**: P0
- **Preconditions**: Valid `SECRET_KEY` in settings
- **Steps**:
  1. Call `create_access_token(user_id="abc-123", role="USER")`
  2. Decode the returned token using `jose.jwt.decode`
- **Expected**: Payload contains `sub="abc-123"`, `role="USER"`, `type="access"`, has `exp` claim

### UNIT-SEC-005: create_refresh_token returns a JWT with type='refresh'
- **Priority**: P1
- **Preconditions**: Valid `SECRET_KEY` in settings
- **Steps**:
  1. Call `create_refresh_token(user_id="abc-123")`
  2. Decode the returned token
- **Expected**: Payload contains `sub="abc-123"`, `type="refresh"`, has `exp` claim

### UNIT-SEC-006: decode_token raises 401 on expired token
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Create a token with `exp` set to a past timestamp
  2. Call `decode_token(expired_token)`
- **Expected**: Raises `HTTPException` with `status_code=401`

### UNIT-SEC-007: decode_token raises 401 on tampered/invalid token
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Call `decode_token("not.a.valid.jwt")`
- **Expected**: Raises `HTTPException` with `status_code=401`

---

## Unit Tests — Schemas (`tests/unit/test_auth_schemas.py`)

### UNIT-SCHEMA-001: RegisterRequest rejects invalid email and short password
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Instantiate `RegisterRequest(email="not-an-email", password="short", full_name="Test")`
  2. Instantiate `RegisterRequest(email="test@example.com", password="1234567", full_name="Test")` (7 chars)
- **Expected**: Both raise `ValidationError`

### UNIT-SCHEMA-002: RegisterRequest rejects empty full_name
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Instantiate `RegisterRequest(email="test@example.com", password="password123", full_name="")`
- **Expected**: Raises `ValidationError`

### UNIT-SCHEMA-003: RegisterRequest accepts valid inputs
- **Priority**: P1
- **Preconditions**: None
- **Steps**:
  1. Instantiate `RegisterRequest(email="test@example.com", password="password123", full_name="Test User")`
- **Expected**: Instance created without errors, fields match

### UNIT-SCHEMA-004: LoginRequest rejects empty password
- **Priority**: P1
- **Preconditions**: None
- **Steps**:
  1. Instantiate `LoginRequest(email="test@example.com", password="")`
- **Expected**: Raises `ValidationError`

---

## Service Tests (`tests/unit/test_auth_service.py`)

### SVC-AUTH-001: register creates a user with hashed password
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns `None`
- **Steps**:
  1. Call `auth_service.register(email="test@example.com", password="password123", full_name="Test")`
- **Expected**: `user_repo.create` called once; the `password_hash` arg ≠ `"password123"` (is bcrypt hash)

### SVC-AUTH-002: register raises 409 on duplicate email
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns an existing `User` object
- **Steps**:
  1. Call `auth_service.register(email="existing@example.com", password="password123", full_name="Test")`
- **Expected**: Raises `HTTPException(status_code=409)`

### SVC-AUTH-003: login returns tokens and saves refresh_token_hash
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns a valid active user; `verify_password` returns True
- **Steps**:
  1. Call `auth_service.login(email="test@example.com", password="password123")`
- **Expected**: Returns `TokenResponse` with non-empty `access_token` and `refresh_token`; `user_repo.update` called with `refresh_token_hash` set

### SVC-AUTH-004: login raises 401 for wrong password
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns a valid user; `verify_password` returns False
- **Steps**:
  1. Call `auth_service.login(email="test@example.com", password="wrong")`
- **Expected**: Raises `HTTPException(status_code=401)`, detail `"Invalid credentials"`

### SVC-AUTH-005: login raises 401 if user not found
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns `None`
- **Steps**:
  1. Call `auth_service.login(email="nobody@example.com", password="any")`
- **Expected**: Raises `HTTPException(status_code=401)`, detail `"Invalid credentials"`

### SVC-AUTH-006: login raises 403 if user is blocked
- **Priority**: P0
- **Preconditions**: Mock `user_repo.get_by_email` returns a user with `is_active=False`
- **Steps**:
  1. Call `auth_service.login(email="test@example.com", password="password123")`
- **Expected**: Raises `HTTPException(status_code=403)`, detail `"Account has been blocked"`

### SVC-AUTH-007: login raises 400 if OAuth user tries password login
- **Priority**: P1
- **Preconditions**: Mock returns user with `auth_provider=AuthProvider.GOOGLE`, `password_hash=None`
- **Steps**:
  1. Call `auth_service.login(email="oauth@example.com", password="any")`
- **Expected**: Raises `HTTPException(status_code=400)`, detail contains provider name

### SVC-AUTH-008: refresh issues new tokens and updates refresh_token_hash
- **Priority**: P0
- **Preconditions**: Valid refresh token for a user; `user.refresh_token_hash` matches token hash
- **Steps**:
  1. Call `auth_service.refresh_tokens(refresh_token=valid_token)`
- **Expected**: Returns new `TokenResponse`; `user_repo.update` called with new `refresh_token_hash`

### SVC-AUTH-009: refresh raises 401 on hash mismatch (token reuse detected)
- **Priority**: P0
- **Preconditions**: Valid JWT but `user.refresh_token_hash` doesn't match token hash
- **Steps**:
  1. Call `auth_service.refresh_tokens(refresh_token=old_token)`
- **Expected**: Raises `HTTPException(status_code=401)`

### SVC-AUTH-010: get_current_user returns user for valid access token
- **Priority**: P1
- **Preconditions**: Valid access token; mock `user_repo.get_by_id` returns a user
- **Steps**:
  1. Call `auth_service.get_current_user(token=valid_access_token)`
- **Expected**: Returns the `User` object

---

## API Tests (`tests/integration/test_auth_api.py`)

### API-AUTH-001: POST /register → 201 with user data
- **Priority**: P0
- **Preconditions**: Fresh test DB (no user with email)
- **Steps**:
  1. `POST /api/v1/auth/register` with `{email, password, full_name}`
- **Expected**: `201`, body contains `data.email`, `data.id`, password NOT in response

### API-AUTH-002: POST /register → 409 on duplicate email
- **Priority**: P0
- **Preconditions**: User with that email already exists
- **Steps**:
  1. `POST /api/v1/auth/register` with same email
- **Expected**: `409`, `detail="Email already registered"`

### API-AUTH-003: POST /register → 422 on invalid input
- **Priority**: P1
- **Preconditions**: None
- **Steps**:
  1. `POST /api/v1/auth/register` with `{email: "invalid", password: "short"}`
- **Expected**: `422 Unprocessable Entity`

### API-AUTH-004: POST /login → 200 with tokens
- **Priority**: P0
- **Preconditions**: Registered user
- **Steps**:
  1. `POST /api/v1/auth/login` with `{email, password}`
- **Expected**: `200`, body has `access_token`, `refresh_token`, `token_type="bearer"`

### API-AUTH-005: POST /login → 401 on wrong password
- **Priority**: P0
- **Preconditions**: Registered user
- **Steps**:
  1. `POST /api/v1/auth/login` with correct email, wrong password
- **Expected**: `401`, `detail="Invalid credentials"`

### API-AUTH-006: POST /login → 401 on unknown email
- **Priority**: P0
- **Preconditions**: No user with this email
- **Steps**:
  1. `POST /api/v1/auth/login` with unknown email
- **Expected**: `401`, generic detail (same as wrong password — no enumeration)

### API-AUTH-007: GET /me → 200 with user profile
- **Priority**: P0
- **Preconditions**: Registered, logged in, valid access token
- **Steps**:
  1. `GET /api/v1/auth/me` with `Authorization: Bearer <token>`
- **Expected**: `200`, body has `data.email`, `data.role`, no `password_hash`

### API-AUTH-008: GET /me → 401 with no token
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. `GET /api/v1/auth/me` with no Authorization header
- **Expected**: `401`

### API-AUTH-009: GET /me → 401 with expired token
- **Priority**: P1
- **Preconditions**: An expired access token
- **Steps**:
  1. `GET /api/v1/auth/me` with `Authorization: Bearer <expired_token>`
- **Expected**: `401`

### API-AUTH-010: POST /refresh → 200 with new token pair
- **Priority**: P1
- **Preconditions**: A valid refresh token from a login
- **Steps**:
  1. `POST /api/v1/auth/refresh` with `{refresh_token}`
- **Expected**: `200`, new `access_token` and `refresh_token` returned

### API-AUTH-011: POST /refresh → 401 with invalid token
- **Priority**: P1
- **Preconditions**: None
- **Steps**:
  1. `POST /api/v1/auth/refresh` with `{refresh_token: "garbage"}`
- **Expected**: `401`
