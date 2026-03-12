# Tech Stack & Setup

## Core Framework

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | FastAPI | latest | Async REST API, dependency injection |
| **Language** | Python | 3.12 | Type hints, modern async/await |
| **Frontend** | Next.js | 16.x | App Router, SSR, client/server components |
| **Frontend Lang** | TypeScript | 5.x | Type safety throughout |
| **Styling** | Tailwind CSS | 4.x | Utility-first CSS |
| **ORM** | SQLAlchemy | 2.0 (async) | Async sessions, `Mapped[]` annotations |
| **Database** | PostgreSQL | 16.x | Primary data store, JSONB columns |
| **Cache** | Redis | 7.x | Session caching, rate limiting |
| **Migrations** | Alembic | latest | Schema versioning from day one |
| **Package** | `pyproject.toml` | — | Modern Python packaging |

---

## Key Backend Libraries

| Category | Library | Purpose |
|----------|---------|---------|
| Auth | python-jose | JWT token creation & verification |
| Password | bcrypt (passlib) | Password hashing |
| AI/LLM | LiteLLM | Multi-provider: OpenAI, Anthropic, Google |
| Payments | stripe | Subscription management, webhooks |
| Email | resend | Verification & password reset emails |
| HTTP Client | httpx | Async HTTP requests (for tools, scraping) |
| HTML Parsing | beautifulsoup4 | Web scraping for knowledge base |
| File Parsing | PyPDF2, python-docx | PDF & DOCX text extraction |
| Settings | pydantic-settings | `.env` loading, validation, type coercion |
| Rate Limiting | slowapi | Request throttling for public endpoints |
| Encryption | cryptography (Fernet) | Credential encryption for integrations |

---

## Key Frontend Libraries

| Category | Library | Purpose |
|----------|---------|---------|
| State Mgmt | Zustand | Lightweight client-side state |
| HTTP | Axios | API calls with interceptors for auth |
| Forms | React Hook Form + Zod | Form state + schema validation |
| Data Fetching | TanStack Query v5 | Server state, caching, background refetch |
| Charts | Recharts | Analytics dashboard charts |
| Icons | Lucide React | Icon library |

---

## Test-Driven Development (TDD)

This project follows TDD. **No production code is written without a failing test first.**

### The Rule

```
Red → Green → Refactor

1. Write a failing test that describes the behaviour you want
2. Write the minimum code to make it pass
3. Refactor while keeping tests green
4. Commit test + implementation together
```

### Where TDD Applies

| Layer | TDD Priority | Why |
|-------|-------------|-----|
| `app/core/security.py` | **Critical** | JWT, password hashing, token verification |
| `app/services/auth_service.py` | **Critical** | Registration, login, email verification |
| `app/services/chat_engine.py` | **Critical** | LLM pipeline, session tracking, tool calling |
| `app/services/billing_service.py` | **Critical** | Plan limits, Stripe integration |
| `app/services/llm_client.py` | **High** | LiteLLM wrapper, provider abstraction |
| `app/services/tools/*.py` | **High** | Tool execution, web search, lead catching |
| `app/services/knowledge_service.py` | **High** | Document parsing, RAG context |
| `app/repositories/*.py` | **High** | Data access layer (testable with mocks) |
| `app/api/v1/*.py` | **Medium** | Route handlers (thin controllers) |

### Example — TDD for Password Hashing

```python
# tests/unit/test_security.py  ← write this FIRST

def test_hash_password_returns_hash():
    """A hashed password should NOT equal the original."""
    hashed = hash_password("mypassword123")
    assert hashed != "mypassword123"
    assert len(hashed) > 50  # bcrypt hashes are long

def test_verify_password_correct():
    hashed = hash_password("mypassword123")
    assert verify_password("mypassword123", hashed) is True

def test_verify_password_incorrect():
    hashed = hash_password("mypassword123")
    assert verify_password("wrongpassword", hashed) is False

# app/core/security.py  ← implement AFTER tests are written
```

---

## Testing Stack

| Tool | Purpose |
|------|---------|
| **pytest** | Test runner |
| **pytest-asyncio** | Async test support |
| **httpx** | Async test client for FastAPI |
| **unittest.mock** | Mocking dependencies |
| **factory-boy** | Test data factories (optional) |

### Testing Strategy by Layer

| Layer | Tool | Mocking |
|-------|------|---------|
| Pure utils (`security.py`, `encryption.py`) | pytest | None — pure functions |
| Services (`services/*.py`) | pytest | Mock repositories |
| Repositories (`repositories/*.py`) | pytest | Test database (SQLite or test PostgreSQL) |
| API routes (`api/v1/*.py`) | pytest + httpx.AsyncClient | Mock services |
| Full user flows | httpx.AsyncClient | Test database |

### Test File Structure

```
backend/
├── tests/
│   ├── conftest.py           # Shared fixtures (db, client, auth)
│   ├── unit/
│   │   ├── test_security.py
│   │   ├── test_auth_service.py
│   │   ├── test_chat_engine.py
│   │   └── ...
│   └── integration/
│       ├── test_auth_api.py
│       ├── test_agents_api.py
│       └── ...
```

### Key Test Patterns

```python
# 1. Async test fixture for database
@pytest_asyncio.fixture
async def db_session():
    async with async_session() as session:
        yield session
        await session.rollback()

# 2. Factory fixture for creating test users
@pytest.fixture
def create_user(db_session):
    async def _create(email="test@example.com", password="test123"):
        user = User(email=email, password_hash=hash_password(password))
        db_session.add(user)
        await db_session.commit()
        return user
    return _create

# 3. Auth helper for protected endpoints
@pytest.fixture
def auth_headers(create_user):
    async def _headers(user=None):
        if not user:
            user = await create_user()
        token = create_access_token({"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}
    return _headers

# 4. Mock external services
@pytest.fixture
def mock_litellm(monkeypatch):
    async def mock_completion(**kwargs):
        return {"choices": [{"message": {"content": "Mocked reply"}}]}
    monkeypatch.setattr("litellm.acompletion", mock_completion)
```

---

## Development Commands

```bash
# Backend
cd backend/
python -m pytest                      # Run all tests
python -m pytest tests/unit/         # Run unit tests only
python -m pytest -x -v               # Stop on first failure, verbose
uvicorn app.main:app --reload        # Start dev server

# Database
alembic upgrade head                  # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration

# Frontend
cd frontend/
npm run dev                           # Start Next.js dev server
npm run build                         # Production build
npm run lint                          # ESLint
```

---

## Local Setup

```bash
# 1. Clone and install
git clone <repo-url>
cd botlixio-v2

# 2. Backend setup
cd backend/
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env
# Fill in DATABASE_URL, SECRET_KEY, etc.

# 4. Start services (PostgreSQL + Redis)
docker compose up -d postgres redis

# 5. Setup database
alembic upgrade head

# 6. Run dev server
uvicorn app.main:app --reload --port 8000

# 7. Frontend (separate terminal)
cd frontend/
npm install
npm run dev
```

---

## Docker (Production)

```bash
# Build and run all services
docker compose -f docker/docker-compose.prod.yml up --build
```

Multi-stage Dockerfiles for backend, frontend, and WhatsApp bridge. Nginx reverse proxy with SSL via Certbot.

---

## Environment Variables

```bash
# Database
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/botlixio"

# Auth
SECRET_KEY=""              # Generate: openssl rand -hex 32
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM (Admin-configured, used as defaults)
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
GOOGLE_API_KEY=""

# Stripe
STRIPE_SECRET_KEY=""
STRIPE_WEBHOOK_SECRET=""
STRIPE_PUBLISHABLE_KEY=""

# Email (Resend)
RESEND_API_KEY=""
EMAIL_FROM="noreply@botlixio.com"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Integration Encryption
FERNET_KEY=""              # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Frontend
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_APP_NAME="Botlixio"

# CORS
CORS_ORIGINS="http://localhost:3000"
```

---

## Folder Conventions

- Backend routes: `app/api/v1/{module}.py` — thin controllers
- Services: `app/services/{module}_service.py` or `app/services/{module}.py` — business logic
- Repositories: `app/repositories/{module}_repo.py` — data access only
- Models: `app/models/{module}.py` — SQLAlchemy 2.0 `Mapped[]` style
- Schemas: `app/schemas/{module}.py` — Pydantic request/response models
- Tests: `tests/unit/` for unit, `tests/integration/` for API tests
