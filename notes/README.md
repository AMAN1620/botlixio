# Notes — Botlixio Learning Journal

Personal notes captured while building Botlixio v2. Each file covers one topic, grounded in real code from this project.

---

## Backend Notes (`notes/backend/`)

### Phase 0 — Project Scaffolding

| File | Topic | Updated |
|------|-------|---------|
| [python-packaging.md](backend/python-packaging.md) | pyproject.toml, venv, pip | 2026-03-13 |
| [fastapi-basics.md](backend/fastapi-basics.md) | FastAPI app factory, CORS, routing | 2026-03-13 |
| [testing-fastapi.md](backend/testing-fastapi.md) | pytest, pytest-asyncio, conftest | (updated: 2026-03-15) |
| [docker-basics.md](backend/docker-basics.md) | Docker Compose, PostgreSQL, Redis | 2026-03-13 |
| [environment-variables.md](backend/environment-variables.md) | .env, .env.example, secrets | 2026-03-13 |

### Phase 1 — Configuration & Database Foundation

| File | Topic | Updated |
|------|-------|---------|
| [pydantic-settings.md](backend/pydantic-settings.md) | Pydantic Settings, config validation, `lru_cache` singleton | (updated: 2026-03-14) |
| [sqlalchemy-async.md](backend/sqlalchemy-async.md) | SQLAlchemy 2.0, `Mapped[]`, async engine, sessions, relationships | (updated: 2026-03-15) |
| [alembic-migrations.md](backend/alembic-migrations.md) | Alembic setup, autogenerate, upgrade/downgrade | (updated: 2026-03-14) |

### Phase 2 — Authentication (Core)

| File | Topic | Updated |
|------|-------|---------|
| [auth-and-security.md](backend/auth-and-security.md) | bcrypt, python-jose, stateful JWTs, `jti` collisions | (updated: 2026-03-15) |

## Frontend Notes (`notes/frontend/`)

### Phase 0 — Project Scaffolding

| File | Topic | Updated |
|------|-------|---------|
| [nextjs-setup.md](frontend/nextjs-setup.md) | create-next-app, project structure | 2026-03-13 |

---

> Run `/update-notes` after each coding session to keep these up to date.
