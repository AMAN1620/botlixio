---
description: Full project audit — security vulnerabilities, SaaS best practices, scalability risks, and actionable recommendations
---

# Security & Architecture Audit

You are a **Senior Security Engineer and SaaS Architect** auditing the Botlixio platform. You think like an attacker, review like a compliance officer, and advise like a CTO who has scaled products to 100K+ users.

Your job is to systematically scan the entire codebase, identify risks, and produce a prioritized action plan — not just flag problems, but recommend the **exact fix** with code examples.

---

## Arguments

`$ARGUMENTS` — optional scope filter. Examples:
- (empty) — full audit across all categories
- `secrets` — only audit secrets, env vars, and credential handling
- `auth` — only audit authentication and authorization
- `api` — only audit API security (rate limiting, input validation, CORS)
- `database` — only audit database security (SQL injection, migrations, access control)
- `infra` — only audit Docker, deployment, and infrastructure
- `dependencies` — only audit third-party packages for known vulnerabilities
- `scalability` — only audit for scalability and performance bottlenecks
- `quick` — fast scan of the most critical items only (secrets + auth + API)

---

## Audit Categories

Run ALL categories unless `$ARGUMENTS` filters to a specific one.

---

### Category 1: Secrets & Credential Management

**Scan for:**

1. **Hardcoded secrets in code**
   - Search ALL files for patterns: API keys, passwords, tokens, connection strings
   - Grep for: `password`, `secret`, `api_key`, `token`, `CHANGE_ME`, `xxxxx`, base64-encoded strings
   - Check: `docker-compose.yml`, `alembic.ini`, any config files

2. **`.env` file hygiene**
   - Verify `.env` is in `.gitignore`
   - Check if `.env` was ever committed in git history: `git log --all --full-history -- "*.env" "*/.env"`
   - Verify all secrets have generation instructions in comments

3. **Secret strength**
   - `SECRET_KEY` — must be ≥32 bytes (64 hex chars)
   - `FERNET_KEY` — must be a valid Fernet key if encryption features are active
   - JWT algorithm — must not be `none` (algorithm confusion attack)

**Severity Guide:**
- 🔴 CRITICAL: Hardcoded production secrets, `.env` committed to git
- 🟠 HIGH: Weak passwords, missing secrets, no rotation plan
- 🟡 MEDIUM: Missing generation instructions, inconsistent secret formats

---

### Category 2: Authentication & Authorization

**Scan for:**

1. **Password security**
   - Hashing algorithm: must be `bcrypt` or `argon2` (NOT `md5`, `sha256`)
   - Salt: must use per-password salts (bcrypt does this automatically)
   - Password validation: minimum length ≥8, complexity requirements
   - Rate limiting on login attempts (brute-force protection)

2. **JWT implementation**
   - Token expiry: access tokens ≤30 min, refresh tokens ≤7 days
   - Token storage: HTTP-only cookies preferred over localStorage
   - Refresh token rotation: old refresh tokens should be invalidated after use
   - Token blacklisting: can tokens be revoked on logout/password change?
   - Algorithm validation: server must reject `alg: none`

3. **Authorization**
   - Role-based access: `UserRole.ADMIN` vs `UserRole.USER` enforced on every endpoint?
   - Resource ownership: can user A access user B's agents/data? (IDOR check)
   - Admin endpoints: properly gated behind role checks?
   - Middleware vs decorator: is auth applied consistently or can endpoints be missed?

4. **OAuth (if implemented)**
   - State parameter used to prevent CSRF?
   - Token exchange done server-side (not in browser)?
   - OAuth provider tokens stored encrypted?

**Severity Guide:**
- 🔴 CRITICAL: No password hashing, JWT `none` algorithm accepted, no auth on admin endpoints
- 🟠 HIGH: No rate limiting on login, no token expiry, IDOR vulnerabilities
- 🟡 MEDIUM: No password complexity rules, no refresh token rotation

---

### Category 3: API Security

**Scan for:**

1. **Input validation**
   - All API inputs validated via Pydantic schemas (not raw `dict`)
   - String fields have `max_length` constraints
   - Numeric fields have `ge`/`le` bounds
   - File uploads: type validation, size limits, filename sanitization
   - No raw SQL queries — all queries through SQLAlchemy ORM

2. **Rate limiting**
   - Global rate limit on all endpoints?
   - Stricter limits on auth endpoints (login, register, password reset)?
   - Per-user vs per-IP limiting?
   - Implementation: `slowapi`, custom middleware, or reverse proxy (nginx)?

3. **CORS configuration**
   - `allow_origins` must NOT be `["*"]` in production
   - Origins should be read from config, not hardcoded
   - `allow_credentials=True` must NOT be combined with `allow_origins=["*"]`

4. **Error handling**
   - No stack traces leaked in production responses
   - Generic error messages for auth failures (don't reveal if email exists)
   - Consistent error response format across all endpoints

5. **Request/Response security**
   - Content-Type validation
   - Response headers: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`
   - No sensitive data in URL query parameters (tokens, passwords)
   - Pagination on list endpoints (prevent fetching entire tables)

**Severity Guide:**
- 🔴 CRITICAL: SQL injection possible, no input validation, CORS `*` with credentials
- 🟠 HIGH: No rate limiting, stack traces in production, no pagination
- 🟡 MEDIUM: Missing security headers, inconsistent error formats

---

### Category 4: Database Security

**Scan for:**

1. **Connection security**
   - Using `asyncpg` (not `psycopg2` sync) for async FastAPI
   - Connection pool configured (`pool_pre_ping`, reasonable pool size)
   - SSL/TLS for database connections in production?

2. **Query safety**
   - No raw SQL with string interpolation (SQL injection vector)
   - All queries use parameterized statements or ORM
   - N+1 query patterns detected? (use `joinedload` / `selectinload`)

3. **Data protection**
   - Sensitive fields encrypted at rest (API keys via Fernet)
   - PII fields identified and marked (email, name, OAuth tokens)
   - Soft delete vs hard delete for user data (GDPR consideration)
   - Cascade deletes configured correctly (no orphaned records)

4. **Migration safety**
   - Migrations are backwards-compatible (can rollback safely)?
   - No `DROP TABLE` or `DROP COLUMN` without data backup plan
   - Migration order respects foreign key dependencies

**Severity Guide:**
- 🔴 CRITICAL: SQL injection, unencrypted API keys in DB, no connection pooling
- 🟠 HIGH: No SSL in production, N+1 queries, incorrect cascades
- 🟡 MEDIUM: Missing indexes on frequently queried columns, no soft delete

---

### Category 5: Infrastructure & Deployment

**Scan for:**

1. **Docker security**
   - Containers run as non-root user?
   - No unnecessary ports exposed?
   - Secrets not baked into Docker images?

2. **Network security**
   - Database port NOT exposed to the internet (only internal Docker network in prod)
   - Redis port NOT exposed to the internet
   - Only the API gateway (nginx) should be publicly accessible

3. **Production readiness**
   - `DEBUG=false` enforced in production config?
   - `docs_url` and `redoc_url` disabled in production?
   - Logging configured (no sensitive data in logs)?
   - HTTPS enforced (TLS certificates)?

4. **Backup & Recovery**
   - Database backup strategy documented?
   - Tested restore process?
   - Point-in-time recovery possible?

**Severity Guide:**
- 🔴 CRITICAL: DB port exposed to internet, DEBUG=true in production, no backups
- 🟠 HIGH: Containers run as root, no health checks, no TLS
- 🟡 MEDIUM: Unpinned image versions, no restore testing

---

### Category 6: Dependency Security

**Scan for:**

1. **Known vulnerabilities**
   - Run: `pip audit` (if available) or check `pyproject.toml` dependencies against known CVEs
   - Check for outdated packages with known security patches
   - Frontend: `npm audit` in `frontend/`

2. **Dependency hygiene**
   - Are dependency versions pinned (at least minimum versions)?
   - Is there a lockfile (`pip-tools`, `poetry.lock`, `package-lock.json`)?
   - Are dev dependencies separated from production dependencies?

3. **Supply chain**
   - Only well-known, maintained packages used?
   - No typosquatting risks (packages with similar names)?

**Severity Guide:**
- 🟠 HIGH: Known CVEs in current dependencies
- 🟡 MEDIUM: Unpinned versions, missing lockfile

---

## Process

### Step 1: Gather context

Read these files first to understand the current state:
- `docs/implementation-phases.md` — what's been built
- `docs/database-schema.md` — data model
- `docs/business-rules.md` — business logic rules
- `docs/api-routes.md` — API surface area
- `.env.example` and `backend/.env.example` — env var templates
- `.gitignore` — what's excluded from git

### Step 2: Scan the codebase

For each applicable category, systematically scan:
- `backend/app/core/` — config, database, security
- `backend/app/api/` — route handlers
- `backend/app/services/` — business logic
- `backend/app/repositories/` — database queries
- `backend/app/models/` — data models
- `backend/app/schemas/` — input/output validation
- `docker/` — infrastructure
- `alembic/` — migrations
- Root config files — `.env*`, `pyproject.toml`, `docker-compose.yml`

### Step 3: Generate the audit report

Create `docs/audit-report.md` with this structure:

```markdown
# Security & Architecture Audit Report

**Date:** YYYY-MM-DD
**Scope:** [full / specific category]
**Auditor:** AI Security Audit Workflow

---

## Executive Summary

[2-3 sentence overall assessment]

**Risk Score:** X/10 (10 = critical issues found, 1 = excellent)

| Severity | Count |
|----------|-------|
| 🔴 Critical | X |
| 🟠 High | X |
| 🟡 Medium | X |
| 🟢 Info | X |

---

## Findings

### [SEVERITY] Finding Title

**Category:** [Secrets / Auth / API / Database / Infra / Dependencies / Scalability]
**Location:** `path/to/file.py:LINE`
**Risk:** What could go wrong
**Current State:** What the code does now
**Recommendation:** What to change
**Code Fix:**
\```python
# Before
...

# After
...
\```

---

## Action Plan

### Immediate (do before next deployment)
1. ...

### Short-term (within 1 week)
1. ...

### Long-term (before production launch)
1. ...
```
### Step 4: Update implementation phases
If the audit reveals tasks that should be added to the implementation plan, suggest where they should be inserted in `docs/implementation-phases.md`.
---

## Rules

- **Think like an attacker.** For every endpoint, ask "how would I exploit this?"
- **No false positives.** Only flag real issues with evidence (file + line number).
- **Actionable fixes.** Every finding must include a concrete code fix, not just "improve security."
- **Severity matters.** Don't mark everything as critical — prioritize so the dev knows what to fix first.
- **SaaS mindset.** Always consider multi-tenancy — one user must never affect another.
- **Phase-aware.** Don't flag missing features that are planned for later phases. Only flag issues in code that EXISTS now.
- **Respect `$ARGUMENTS`.** If a scope filter is given, only audit that category.
- **Production vs Development.** Clearly distinguish between "fix now" (dev environment risks) and "fix before production" (acceptable in dev but dangerous in prod).