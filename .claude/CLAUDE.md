# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Botlixio v2** is a full-stack AI Agent Builder SaaS platform. Users create, configure, and deploy custom AI chatbot agents with RAG knowledge bases, tool calling, and multi-channel deployment (widget, WhatsApp, Discord, Slack).

**Architecture**: FastAPI backend (Python 3.12), Next.js 16 frontend (TypeScript), PostgreSQL database, Redis cache. Clean 4-layer architecture: Routes → Services → Repositories → Models.

## Development Commands

### Backend (Python 3.12 + FastAPI)

```bash
# Setup
cd backend/
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env             # Fill in your values

# Database
alembic upgrade head                                  # Apply migrations
alembic revision --autogenerate -m "description"      # Create migration

# Testing (TDD - write tests first!)
python -m pytest                  # Run all tests
python -m pytest tests/unit/      # Run unit tests only
python -m pytest tests/integration/  # Run integration tests
python -m pytest -x -v            # Stop on first failure, verbose
python -m pytest -k "test_name"   # Run specific test

# Run server
uvicorn app.main:app --reload     # http://localhost:8000
# API docs: http://localhost:8000/api/docs
```

### Frontend (Next.js 16 + TypeScript)

```bash
cd frontend/
npm install
npm run dev    # http://localhost:3000
npm run build
npm run lint
```

### Infrastructure

```bash
# Start PostgreSQL + Redis
docker compose -f docker/docker-compose.yml up -d

# Stop services
docker compose -f docker/docker-compose.yml down
```

## Test-Driven Development (TDD)

**This project strictly follows TDD.** No production code without a failing test first.

### The Rule
```
Red → Green → Refactor

1. Write a failing test that describes the behavior
2. Write minimum code to make it pass
3. Refactor while keeping tests green
4. Commit test + implementation together
```

### Priority Levels
- **Critical TDD**: `app/core/security.py`, `app/services/auth_service.py`, `app/services/chat_engine.py`, `app/services/billing_service.py`
- **High TDD**: All services (`app/services/*.py`), all repositories (`app/repositories/*.py`)
- **Medium TDD**: API routes (`app/api/v1/*.py`) - thin controllers

### Test Structure
- `tests/unit/` - Pure function tests, service tests with mocked repositories
- `tests/integration/` - API endpoint tests with test database
- `tests/conftest.py` - Shared fixtures (db session, auth headers, factories)

### Running a Single Test
```bash
# Run specific test function
python -m pytest tests/unit/test_security.py::test_hash_password_returns_hash

# Run specific test file
python -m pytest tests/unit/test_security.py

# Run tests matching pattern
python -m pytest -k "password"
```

## Backend Architecture

### 4-Layer Clean Architecture

1. **Routes** (`app/api/v1/*.py`): Thin controllers - validate input, call service, return response. No business logic.
2. **Services** (`app/services/*.py`): All business logic - plan checks, orchestration, validation. Depend on repositories, not models directly.
3. **Repositories** (`app/repositories/*.py`): Data access only - SQL queries, CRUD operations. No business logic.
4. **Models** (`app/models/*.py`): SQLAlchemy 2.0 models using `Mapped[]` + `mapped_column()` syntax.

### Key Conventions

- **API versioning**: All routes under `/api/v1/` for future compatibility
- **Dependency injection**: Use FastAPI's `Depends()` for db sessions, auth, services
- **Async everywhere**: All database operations use `async`/`await` with asyncpg
- **UUID primary keys**: All models use `uuid.UUID` as primary keys
- **Enums**: Defined in `app/models/enums.py` and used consistently across models/schemas

### Service Layer Patterns

Services orchestrate business logic and depend on repositories:

```python
# Good: Service depends on repository
class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, email: str, password: str) -> User:
        # Business logic here
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExists()
        # More logic...
```

### Database Models (SQLAlchemy 2.0)

Use the modern `Mapped[]` annotation style:

```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

### Authentication & Authorization

- **JWT tokens**: Access token (30 min), refresh token (7 days)
- **Password hashing**: bcrypt via passlib
- **Email verification**: Required before creating agents
- **Role-based access**: `UserRole.ADMIN` (full access) vs `UserRole.USER` (own resources)
- **Resource ownership**: Check `user_id` matches current user for agents, knowledge, etc.

### Subscription & Plan Limits

Plan limits enforced in services before operations:

```python
# In agent_service.py - before creating agent
if subscription.agents_used >= plan.max_agents:
    raise PlanLimitExceeded("agent_limit")

# In chat_engine.py - before processing message
if subscription.messages_used >= plan.max_messages_per_month:
    raise PlanLimitExceeded("message_limit")
```

**Plan tiers**: FREE → STARTER → GROWTH → BUSINESS (see `docs/business-rules.md` for limits)

### Chat Engine Pipeline

The chat engine (`app/services/chat_engine.py`) implements this flow:

1. Receive message
2. Find or create session (keyed by `agent_id` + `session_identifier`)
3. Check plan limits (message count)
4. Load conversation history (last N messages)
5. Build system prompt with RAG knowledge context
6. Call LLM via LiteLLM
7. If tool calls in response → execute tools → feed results → repeat LLM call (max 5 iterations)
8. Save assistant message
9. Increment message counters (subscription + agent)
10. Check for lead data in response → save lead if found
11. Return response

### LLM Integration (LiteLLM)

- LiteLLM provides unified interface for OpenAI, Anthropic, Google models
- Wrapper service: `app/services/llm_client.py` (testable, mockable)
- Admin configures which providers/models available per plan
- BYOK (Bring Your Own Key) available on GROWTH+ plans

### Tool System

Tools use function-calling pattern:
- Tools defined in `app/services/tools/`
- Base interface: `app/services/tools/base.py`
- Registry: `app/services/tools/registry.py`
- Built-in tools: web search, weather, lead catcher
- Maximum 5 tool call iterations per message

### Knowledge Base (RAG)

- Simple concatenation in v1 (vector search planned for v2)
- Supported sources: PDF (PyPDF2), TXT, CSV, DOCX (python-docx), URL (BeautifulSoup), raw text
- Content injected into system prompt before chat
- Limits: 10 MB max file size, 100k chars per item, plan-based item count

## Critical Business Rules

### Agent Status Lifecycle
```
DRAFT → LIVE (deploy)
LIVE → PAUSED (pause)
PAUSED → LIVE (resume)
```
- Only LIVE agents respond to chat
- PAUSED agents return fallback message
- DRAFT agents not accessible via public endpoints

### Session Management
- Widget sessions: `session_identifier` = client IP
- WhatsApp: `session_identifier` = phone number
- Discord/Slack: `session_identifier` = platform user ID
- Sessions expire after 24 hours inactivity

### Email Verification Flow
```
1. User registers → is_verified=false
2. Verification email sent (24h expiry)
3. User clicks link → token validated → is_verified=true
4. Unverified users can log in but cannot create agents
```

### Billing & Downgrade Rules
- Downgrades effective at period end
- Excess agents → PAUSED (not deleted)
- Excess knowledge items remain but cannot add more
- Excess workflows → PAUSED
- User must reduce usage to re-activate

### Credential Security
- Integration credentials encrypted with Fernet symmetric encryption
- Encryption key in environment (`FERNET_KEY`)
- Credentials decrypted only during workflow execution, then discarded
- Startup fails if `FERNET_KEY` invalid

## Database Migrations

- **Alembic** for schema versioning from day one
- Auto-generate migrations from model changes: `alembic revision --autogenerate -m "description"`
- Review generated migrations before applying
- Never edit applied migrations - create new ones
- Apply migrations: `alembic upgrade head`

## API Response Standards

### Success (list)
```json
{"data": [...], "total": 100, "page": 1, "page_size": 20}
```

### Success (single)
```json
{"data": { ... }}
```

### Error
```json
{"detail": "Error message"}
```

### HTTP Status Codes
- 200: Success
- 201: Created
- 204: Deleted (no content)
- 400: Validation error
- 401: Unauthenticated
- 403: Forbidden (wrong role / not owner)
- 404: Not found
- 409: Conflict (duplicate email)
- 429: Rate limited
- 500: Internal server error

## File Naming Conventions

- Python files: `snake_case.py`
- TypeScript components: `PascalCase.tsx`
- TypeScript utilities: `camelCase.ts`
- Config files: `kebab-case.ts`

## Environment Variables

Critical env vars (see `.env.example` for full list):
- `DATABASE_URL`: PostgreSQL connection string (asyncpg driver)
- `SECRET_KEY`: JWT signing key (generate: `openssl rand -hex 32`)
- `FERNET_KEY`: Integration credential encryption key
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`: Admin LLM keys
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`: Billing integration
- `RESEND_API_KEY`: Email service
- `REDIS_URL`: Cache and rate limiting

## Important Documentation

- Full architecture: `docs/README.md`
- Database schema: `docs/database-schema.md`
- Business rules: `docs/business-rules.md`
- API routes: `docs/api-routes.md`
- Tech stack: `docs/tech-stack.md`
- Folder structure: `docs/folder-structure.md`
- Feature specs: `docs/features/*.md`

## Common Pitfalls

1. **Writing code before tests**: This violates TDD. Always write failing tests first.
2. **Business logic in routes**: Routes should be thin controllers. Put logic in services.
3. **Direct model imports in routes**: Routes should depend on services, services on repositories, repositories on models.
4. **Forgetting plan limit checks**: Always check subscription limits in services before operations.
5. **Not verifying resource ownership**: Check `user_id` matches current user for agents, knowledge, workflows.
6. **Hardcoding model names**: Use plan's `allowed_models` list; respect BYOK override.
7. **Missing async/await**: All database operations must be async.
8. **Not handling LLM failures**: Always wrap LiteLLM calls in try/except, return fallback on error.
9. **Exposing internal errors to users**: Catch exceptions in routes, return user-friendly messages.
10. **Forgetting to increment counters**: Update `subscription.messages_used`, `agent.total_messages` after chat.

## Multi-Channel Architecture

All channels (widget, WhatsApp, Discord, Slack) normalize to unified format:
```python
{
    "channel": "whatsapp" | "discord" | "slack",
    "sender_id": "phone_number" | "discord_user_id" | "slack_user_id",
    "message": "text content",
    "agent_id": "uuid",
    "metadata": { ... }
}
```

Process through same chat engine, send response via channel-specific API.

## Frontend Architecture (Next.js 16)

- **App Router** (not Pages Router)
- **No src/ directory**: `app/` at root level
- Route groups: `(auth)/` for auth pages, `(dashboard)/` for protected pages
- Server components by default, client components with `'use client'`
- State: Zustand for client state, TanStack Query for server state
- Forms: React Hook Form + Zod validation
- Styling: Tailwind CSS 4.x

## Rate Limiting

- **Public widget**: 10 msg/min per IP (chat), 30 req/min (status)
- **Authenticated chat**: 30 msg/min per user
- **Agent CRUD**: 60 req/min per user
- **Knowledge upload**: 10 uploads/min per user

## Security Practices

- Never log or expose: passwords, JWT secrets, API keys, Fernet keys
- Always validate user owns resource before operations
- Encrypt sensitive credentials (integrations) with Fernet
- Use parameterized queries (SQLAlchemy ORM prevents SQL injection)
- Validate all user input with Pydantic schemas
- CORS configured for frontend origin only
- Rate limit public endpoints
