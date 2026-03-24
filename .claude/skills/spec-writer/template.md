# Spec: {Module Name}

**Mode**: Retroactive | Proactive
**Phase**: {N}
**Routes**: GET /api/v1/{module}, POST /api/v1/{module}, ...
**Access**: Public | Authenticated user | Admin only

**Files**:
- `backend/app/api/v1/{module}.py` — route handlers
- `backend/app/services/{module}_service.py` — business logic
- `backend/app/schemas/{module}.py` — request/response schemas
- `backend/app/repositories/{module}_repo.py` — data access

---

## Overview

{2–3 sentences: what this module does and why it exists}

## User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-01 | registered user | log in with email+password | I can access my dashboard |

## Happy Flows

### Flow 1: {name}
1. User sends POST /api/v1/auth/login with email + password
2. System verifies password hash
3. System returns 200 with access_token + refresh_token

## Edge Cases

| Scenario | Expected Behaviour |
|----------|--------------------|
| Wrong password | 401 Unauthorized |
| Account not verified | 403 Forbidden |
| Email not found | 401 (don't reveal existence) |

## Pydantic Schemas

```python
# Paste verbatim from source (retroactive) or proposed (proactive)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

## API Contract

### POST /api/v1/auth/login

**Access**: Public

**Request body**:
```json
{ "email": "user@example.com", "password": "secret123" }
```

**Responses**:
| Code | Condition | Body |
|------|-----------|------|
| 200 | Success | `{ "data": { "access_token": "...", "refresh_token": "..." } }` |
| 401 | Bad credentials | `{ "detail": "Invalid credentials" }` |
| 422 | Validation error | `{ "detail": [...] }` |

## Acceptance Criteria

- [ ] All happy flows return correct status codes and response shapes
- [ ] Edge cases return appropriate error codes
- [ ] Auth/role checks enforced on every protected endpoint

## Deferred / Not Yet Implemented *(retroactive only)*

- {Feature documented in feature doc but not yet built}
