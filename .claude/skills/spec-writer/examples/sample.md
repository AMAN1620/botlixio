# Example — Real spec from this project

Extracted from `docs/specs/auth-extended.SPEC.md`. Shows the expected style.

---

## Header

```markdown
# Spec: Authentication (Extended)

**Mode**: Retroactive
**Phase**: 1
**Routes**: POST /api/v1/auth/register, POST /api/v1/auth/login, POST /api/v1/auth/refresh, POST /api/v1/auth/logout, GET /api/v1/auth/me, POST /api/v1/auth/verify-email, POST /api/v1/auth/resend-verification
**Access**: Mixed (Public + Authenticated)

**Files**:
- `backend/app/api/v1/auth.py` — route handlers
- `backend/app/services/auth_service.py` — business logic
- `backend/app/schemas/auth.py` — request/response schemas
- `backend/app/repositories/user_repo.py` — data access
- `backend/app/core/security.py` — JWT + password hashing utilities
```

## Key patterns to follow

- **Mode stated upfront** — Retroactive vs Proactive changes how you write
- **All routes listed** — every endpoint this module owns
- **Access level** — Public, Authenticated, Admin, or Mixed
- **File paths** — exact paths in the project, not generic placeholders
- **No test scenarios** — those belong in TEST-CASES.md (produced by `/tdd-plan`)
- **Deferred section** — only in retroactive mode, lists things from the feature doc that aren't built yet
