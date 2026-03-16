# Security & Architecture Audit Report

**Date:** 2026-03-15
**Scope:** Full
**Auditor:** AI Security Audit Workflow

---

## Executive Summary

Botlixio is still early-stage and the implemented backend surface is small, which limits immediate blast radius. The highest-risk gaps are around API hardening and production posture rather than cryptography: auth endpoints are not rate-limited, refresh tokens are returned in JSON instead of an `HttpOnly` cookie despite the documented rule, API docs are always exposed, and there is no security-headers middleware. There is also configuration fragility: the app can fail to start from a malformed `DEBUG` env value, and secret strength is documented but not enforced.

I did not verify third-party CVEs with `pip audit` / `npm audit` because networked package-audit commands were not available in this environment.

---

## Findings

### HIGH: No rate limiting on auth endpoints

**Evidence**
- `slowapi` is declared as a dependency in `backend/pyproject.toml` but is not wired into the app or routes.
- The implemented auth routes in `backend/app/api/v1/auth.py` expose `POST /register`, `POST /login`, and `POST /refresh` without request throttling.

**Risk**
- Enables brute-force login attempts, credential stuffing, registration abuse, and refresh-token abuse.

**Recommendation**
- Add per-IP limits at minimum:
  - `POST /auth/login`: 5-10/minute
  - `POST /auth/register`: 3-5/minute
  - `POST /auth/refresh`: 20/minute
- For authenticated routes, add optional per-user limits later.

**Fix sketch**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

### HIGH: Refresh tokens are returned in JSON instead of an `HttpOnly` cookie

**Evidence**
- Business rules say refresh tokens are stored in an `httpOnly` cookie.
- Current API returns `TokenResponse` bodies containing both `access_token` and `refresh_token`.

**Risk**
- If the frontend stores refresh tokens in `localStorage` or JS memory, XSS can steal long-lived session credentials.

**Recommendation**
- Keep access token short-lived in the response body if needed.
- Move refresh token to a `Set-Cookie` header with `HttpOnly`, `Secure`, and `SameSite=Lax` or `Strict`.
- Change `/auth/refresh` to read the cookie server-side.

**Fix sketch**
```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=settings.is_production,
    samesite="lax",
    max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
)
```

---

### HIGH: API docs and OpenAPI are always exposed

**Evidence**
- `backend/app/main.py` sets `docs_url`, `redoc_url`, and `openapi_url` unconditionally.

**Risk**
- Makes endpoint discovery easier in production and exposes internal contract details unnecessarily.

**Recommendation**
- Disable docs in production.

**Fix sketch**
```python
app = FastAPI(
    ...,
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None if settings.is_production else "/api/redoc",
    openapi_url=None if settings.is_production else "/api/openapi.json",
)
```

---

### MEDIUM: No security-headers middleware

**Evidence**
- `backend/app/main.py` only adds CORS middleware.
- No middleware sets `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, or HSTS.

**Risk**
- Weaker browser-side hardening and more exposure to common misconfiguration classes.

**Recommendation**
- Add middleware for standard response headers.
- Only enable HSTS in production behind HTTPS.

---

### MEDIUM: Config parsing is fragile enough to break startup

**Evidence**
- `backend/app/core/config.py` types `DEBUG` as `bool`.
- Current local `backend/.env` and/or runtime environment can provide non-boolean values such as `release`, which crashes startup and test collection.

**Risk**
- Availability issue and deployment fragility.
- In practice, teams often overload `DEBUG` with environment names.

**Recommendation**
- Keep `DEBUG` boolean, but validate `ENVIRONMENT` separately and fail with a clearer message.
- Optionally add a `model_validator` to reject invalid combinations with actionable text.

---

### MEDIUM: Secret presence is documented, but secret strength is not enforced

**Evidence**
- `backend/app/core/config.py` accepts any `SECRET_KEY` string and any `FERNET_KEY` string.
- Comments say `SECRET_KEY` should be generated securely, but there is no runtime validation.

**Risk**
- Weak or malformed secrets can silently reach production.

**Recommendation**
- Validate:
  - `SECRET_KEY` length >= 32 bytes or 64 hex chars
  - `ALGORITHM != "none"`
  - `FERNET_KEY`, when set, is parseable by `cryptography.fernet.Fernet`

---

### MEDIUM: Real `.env` files exist in the workspace; templates are missing

**Evidence**
- The repo has `.env` and `backend/.env`.
- The workflow expected `.env.example` templates, but they are not present.
- `.gitignore` excludes `.env*`, and `git ls-files` showed these env files are not tracked.

**Risk**
- Current local state is safer than committed secrets, but onboarding and secret hygiene are weak.
- Missing templates encourage copying real env files around.

**Recommendation**
- Add `.env.example` and `backend/.env.example` with placeholder values only.
- Keep real `.env` files untracked.
- Document secret generation commands next to each variable.

---

### MEDIUM: CORS is configurable, but there is no production guardrail

**Evidence**
- `backend/app/main.py` sets `allow_credentials=True`.
- Origins come from `settings.cors_origins_list`, but there is no check preventing `"*"` in production.

**Risk**
- A bad production env value can create an unsafe CORS posture.

**Recommendation**
- Reject wildcard origins when `allow_credentials=True`.
- Validate `CORS_ORIGINS` at startup in production.

---

### MEDIUM: Development infrastructure exposes Redis and Postgres on host ports

**Evidence**
- `docker/docker-compose.yml` publishes Postgres and Redis to the host.

**Risk**
- Fine for local development, but dangerous if this compose file is reused in a shared or production-like environment.

**Recommendation**
- Keep this file explicitly dev-only.
- Add a separate production deployment definition with internal-only DB/Redis networking.

---

### MEDIUM: Backend dependency versions are open-ended and there is no Python lockfile

**Evidence**
- `backend/pyproject.toml` uses `>=` for all runtime dependencies.
- No backend lockfile was present in the repository scan.

**Risk**
- Reproducibility and supply-chain drift.

**Recommendation**
- Add a lock strategy (`uv.lock`, `poetry.lock`, or pinned requirements).
- Gate dependency updates via CI.

---

### LOW: No logout endpoint yet

**Evidence**
- Refresh token rotation exists, but there is no implemented logout route to clear `refresh_token_hash`.

**Risk**
- Session revocation UX is incomplete.

**Recommendation**
- Add `POST /auth/logout` to null `refresh_token_hash` and clear the refresh cookie.

---

## Positive Notes

- Passwords are hashed with bcrypt via Passlib in `backend/app/core/security.py`.
- JWT decoding explicitly specifies accepted algorithms, which avoids `alg=none` acceptance.
- Refresh-token rotation now persists a hash in the database instead of keeping refresh tokens fully stateless.
- Auth failure messages are mostly generic enough to avoid obvious email enumeration on login.
- Database access currently uses SQLAlchemy ORM / Core constructs rather than interpolated raw SQL.

---

## Prioritized Action Plan

1. Add rate limiting to auth endpoints and public endpoints.
2. Move refresh tokens to `HttpOnly` cookies and add logout.
3. Disable docs/OpenAPI in production and add security headers.
4. Add config validators for `SECRET_KEY`, `FERNET_KEY`, `CORS_ORIGINS`, and clearer env parsing.
5. Add env templates and a backend lockfile.
6. Split dev vs production infrastructure configs so DB/Redis are never exposed by default in production.

---

## Verification Limits

- I did not run `pip audit` or `npm audit` because networked package-vulnerability checks were unavailable here.
- I did not inspect unimplemented future endpoints from the feature docs as if they were live code; findings are based on the current repository state.
