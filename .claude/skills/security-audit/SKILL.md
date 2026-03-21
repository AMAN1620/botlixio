---
name: security-audit
description: >
  Full security and architecture audit for a FastAPI/Python SaaS project. Scans for
  vulnerabilities across secrets, authentication, API security, database, infrastructure,
  and dependencies. Produces a prioritized report with exact file locations and code fixes.
  Use this skill whenever the user asks to audit security, check for vulnerabilities,
  review auth implementation, check if the project is production-ready, or asks "how
  secure is this?". Also trigger for: "run a security audit", "check for security issues",
  "is my auth safe", "review my API security", "check my env vars", "pentest checklist".
---

# Security Audit

Systematic security scan of the codebase. Think like an attacker, report like a compliance
officer, advise like a CTO who has shipped to 100K+ users.

## Scope

`$ARGUMENTS` — optional filter:

| Argument | What gets audited |
|---|---|
| (empty) | Full audit — all categories |
| `secrets` | Env vars, hardcoded credentials, key strength |
| `auth` | Passwords, JWT, RBAC, IDOR |
| `api` | Input validation, rate limiting, CORS, error handling |
| `database` | Query safety, encryption, migrations, indexes |
| `infra` | Docker, network exposure, production config |
| `dependencies` | Known CVEs, outdated packages, lockfiles |
| `quick` | Fast scan: secrets + auth + API only |

---

## Process

### 1. Gather context (read in parallel)

- `docs/implementation-phases.md` — what's been built
- `docs/database-schema.md` — data model
- `docs/business-rules.md` — role and limit rules
- `docs/api-routes.md` — API surface area
- `.env.example` — env var templates
- `.gitignore` — what's excluded

### 2. Scan the codebase

For each applicable category below, scan these paths:

```
backend/app/core/        ← config, database, security
backend/app/api/         ← route handlers
backend/app/services/    ← business logic
backend/app/models/      ← data models
backend/app/schemas/     ← input validation
docker/                  ← infrastructure
alembic/versions/        ← migrations
pyproject.toml           ← dependencies
.env*, docker-compose*   ← config files
```

### 3. Write the audit report

Create `docs/audit-report.md` using the template in the **Report Format** section below.

### 4. Suggest plan additions

If the audit reveals missing security tasks, suggest where to insert them in
`docs/implementation-phases.md`.

---

## Audit Categories

### Secrets & Credentials

```bash
# Grep for hardcoded secrets
grep -rn "password\s*=\s*['\"]" backend/ --include="*.py"
grep -rn "api_key\s*=\s*['\"]" backend/ --include="*.py"
grep -rn "CHANGE_ME\|xxxxx\|secret123\|hardcoded" backend/ --include="*.py"

# Check .env was never committed
git log --all --full-history -- "*.env" "*/.env"
```

Check:
- `SECRET_KEY` ≥ 64 hex chars (32 bytes)
- `FERNET_KEY` is a valid Fernet key
- JWT algorithm is not `none`
- `.env` is in `.gitignore`

Severity: 🔴 Hardcoded production secrets or `.env` in git · 🟠 Weak keys · 🟡 Missing generation instructions

---

### Authentication & Authorization

Check:
- Password hashing: `bcrypt` or `argon2` only (never `md5`/`sha256`)
- JWT: access token ≤ 30 min, refresh token ≤ 7 days
- JWT: server rejects `alg: none`
- Refresh token rotation: old token invalidated after use
- RBAC: `UserRole.ADMIN` vs `UserRole.USER` enforced on every endpoint
- IDOR: can user A access user B's resources? Check every service that fetches by ID

```bash
# Find endpoints missing auth dependency
grep -n "def " backend/app/api/v1/*.py | grep -v "current_user\|Depends"
```

Severity: 🔴 No password hashing, JWT `none` accepted, no auth on admin endpoints · 🟠 No rate limit on login, IDOR vulnerabilities · 🟡 No refresh token rotation

---

### API Security

Check:
- All inputs validated via Pydantic schemas (no raw `dict`)
- String fields have `max_length`
- File uploads: type + size + filename validation
- No raw SQL with string interpolation
- CORS `allow_origins` is not `["*"]` in production
- `allow_credentials=True` not combined with `allow_origins=["*"]`
- No stack traces in error responses
- Pagination on all list endpoints

```bash
# Find potential missing Pydantic validation
grep -n "request.body\|request.json\|dict(" backend/app/api/ -r

# Check CORS config
grep -n "allow_origins\|CORSMiddleware" backend/ -r
```

Severity: 🔴 SQL injection possible, CORS `*` with credentials · 🟠 No rate limiting, stack traces in prod · 🟡 Missing security headers

---

### Database Security

Check:
- `asyncpg` driver used (not sync psycopg2)
- Connection pool configured (`pool_pre_ping=True`)
- No raw SQL with f-strings or `%` formatting
- Sensitive fields encrypted at rest (API keys via Fernet)
- Cascade deletes configured correctly
- N+1 query patterns (use `joinedload`/`selectinload`)
- Migrations are backwards-compatible (no `DROP COLUMN` without backup plan)

```bash
# Find raw SQL
grep -rn "execute.*f\"\|execute.*%s" backend/ --include="*.py"
grep -rn "DROP TABLE\|DROP COLUMN" backend/alembic/ --include="*.py"
```

Severity: 🔴 SQL injection, unencrypted API keys · 🟠 No SSL in prod, N+1 queries · 🟡 Missing indexes

---

### Infrastructure

Check:
- Containers run as non-root user
- Database port NOT exposed publicly (only internal Docker network)
- Redis port NOT exposed publicly
- `DEBUG=false` enforced in production
- `docs_url`/`redoc_url` disabled in production
- No secrets baked into Docker images

```bash
grep -n "DEBUG\|docs_url\|redoc_url" backend/app/core/config.py
grep -n "ports:" docker/docker-compose*.yml
grep -n "USER " docker/Dockerfile 2>/dev/null
```

Severity: 🔴 DB port exposed, DEBUG=true in prod · 🟠 Containers run as root, no TLS · 🟡 Unpinned image versions

---

### Dependencies

```bash
cd backend && pip audit 2>/dev/null || safety check 2>/dev/null
cd frontend && npm audit
```

Check:
- Known CVEs in current versions
- Dev dependencies separated from prod
- Lockfile exists (`pip-tools`/`poetry.lock`/`package-lock.json`)

Severity: 🟠 Known CVEs in current deps · 🟡 Unpinned versions, no lockfile

---

## Report Format

```markdown
# Security & Architecture Audit Report

**Date:** YYYY-MM-DD
**Scope:** full | specific-category
**Auditor:** AI Security Audit

---

## Executive Summary

[2–3 sentence overall assessment]

**Risk Score:** X/10

| Severity | Count |
|----------|-------|
| 🔴 Critical | X |
| 🟠 High | X |
| 🟡 Medium | X |
| 🟢 Info | X |

---

## Findings

### 🔴 [Finding Title]

**Category:** Secrets | Auth | API | Database | Infra | Dependencies
**Location:** `path/to/file.py:LINE`
**Risk:** What an attacker could do
**Current state:** What the code does now
**Fix:**
```python
# Before
old_code

# After
fixed_code
```

---

## Action Plan

### Immediate (fix before next deployment)
1. ...

### Short-term (within 1 week)
1. ...

### Before production launch
1. ...
```

---

## Rules

- No false positives — only flag real issues with file + line number evidence
- Phase-aware — don't flag missing features planned for later phases; only audit code that exists now
- Multi-tenancy mindset — one user must never be able to affect another's data
- Distinguish dev-only risks from production-critical ones
- Every finding needs a concrete code fix, not just "improve security"
- Don't modify source code — diagnostic only
