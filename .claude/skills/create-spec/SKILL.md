---
name: create-spec
description: >
  Creates a detailed SPEC.md for a feature module by reading project docs and the actual
  codebase. Works in two modes: Retroactive (document what was built) or Proactive
  (design guide before implementation). Use this skill whenever the user wants to document
  a feature, write a spec before starting to code, generate a spec from existing code,
  design an API contract, or produce a structured feature specification. Trigger on:
  "create a spec for X", "write a SPEC.md", "document this feature", "spec out the auth
  module", "I need a spec before I start coding", or when the user references a feature
  doc and wants a formal spec written from it.
---

# Create Spec

Produces a `SPEC.md` for a feature module — the single source of truth for what that
feature does, what the API looks like, and what needs to be tested.

## Input

`$ARGUMENTS` — one of:
- Module name: `auth`, `agents`, `chat`, `billing`
- Route path: `/auth`, `/agents`
- Feature doc path: `docs/features/01-authentication.md`
- `all` — generate specs for all modules missing a SPEC.md

If no argument, ask the user which module to spec.

---

## Quick reference

| Step | What happens |
|------|-------------|
| 0. Orient | Detect project layout (API dir, services, schemas, tests, feature docs) |
| 1. Identify | Module name, feature doc, source files |
| 2. Mode | Retroactive (code exists) or Proactive (code doesn't exist yet) |
| 3. Read | Feature doc + API/business rules docs + source files (retroactive) |
| 4. Analyze | Routes, access control, schemas, edge cases, test count |
| 5. Write | SPEC.md using the template below |
| 6. Verify | File paths, response codes, schema names match actual code |
| 7. Report | Summary of what was written |

---

## Step 0: Detect project structure

```bash
# Find API routes
ls backend/app/api/v1/ 2>/dev/null || ls src/routes/ 2>/dev/null || ls app/routes/ 2>/dev/null

# Find services, schemas, repos
ls backend/app/services/ backend/app/schemas/ backend/app/repositories/ 2>/dev/null

# Find feature docs
ls docs/features/ 2>/dev/null || ls docs/ 2>/dev/null || ls specs/ 2>/dev/null
```

Use discovered paths throughout.

---

## Step 2: Mode detection

Check if implementation files exist with real logic (not just stubs):

- **Retroactive** → route handlers, service functions, and schemas exist → document what IS built
- **Proactive** → files don't exist yet → write a forward-looking design guide

State the mode before proceeding.

Check for existing SPEC.md — if found, tell the user its path and stop (unless `redo` was passed).

---

## Step 3: What to read

**Always read** (stop if feature doc is missing):
- Feature doc — business requirements and user stories
- API reference doc (e.g., `docs/api-routes.md`)
- Business rules doc (e.g., `docs/business-rules.md`)
- Database schema doc

**Retroactive — also read:**
- Schema/Pydantic files for this module
- Service file(s)
- Route/controller file(s)
- Repository file(s)
- All test files for this module

Read these in parallel.

---

## SPEC.md template

Output location: `docs/specs/{module}.SPEC.md` or alongside source files — ask if unclear.

```markdown
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

## Test Scenarios

### Unit Tests
- UNIT-AUTH-001: hash_password returns a bcrypt hash different from input
- UNIT-AUTH-002: verify_password returns True for correct password, False for wrong

### Service Tests
- SVC-AUTH-001: login with valid credentials returns tokens
- SVC-AUTH-002: login with wrong password raises InvalidCredentials

### API Tests
- API-AUTH-001: POST /login with valid body returns 200 + tokens
- API-AUTH-002: POST /login with wrong password returns 401

## Acceptance Criteria

- [ ] All happy flows return correct status codes and response shapes
- [ ] Edge cases return appropriate error codes
- [ ] Auth/role checks enforced on every protected endpoint
- [ ] All P0 tests pass

## Deferred / Not Yet Implemented *(retroactive only)*

- OAuth login documented in feature doc but not yet built
```

---

## Step 6: Verify before finishing

- All listed file paths exist (retroactive) or are reasonable (proactive)
- Response codes match actual route handlers
- Schema field names match actual code
- Flag any mismatch found

---

## Rules

- Feature doc is required — stop if you can't find it
- Retroactive mode: document what IS built, not what was planned
- Copy schemas verbatim — never paraphrase field names or types
- Don't invent requirements — all content comes from the feature doc or actual code
- Don't modify any source code — this skill produces SPEC.md only
