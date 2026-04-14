# Botlixio v2

**AI Agent Builder SaaS** — Build, configure, and deploy custom AI chatbot agents across multiple channels (widget, WhatsApp, Discord, Slack).

## Architecture

| Layer | Stack |
|---|---|
| Backend API | FastAPI + Python 3.12 |
| Frontend | Next.js 16 + TypeScript |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 |
| Vector Store | Qdrant |
| Background Jobs | ARQ worker |
| WhatsApp | Node.js microservice (Baileys) |

---

## Prerequisites

- Docker + Docker Compose
- Python 3.12
- Node.js 18+
- `openssl` (for generating secrets)

---

## Setup

### 1. Environment variables

```bash
cp backend/.env.example .env   # root-level .env, read by docker-compose
```

Fill in the values:

| Variable | How to generate |
|---|---|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `FERNET_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `INTERNAL_SECRET` | Any random string, shared between backend and WhatsApp service |
| `OPENAI_API_KEY` | Your OpenAI key (required for chat) |
| `RESEND_API_KEY` | For transactional emails (email verification) |

### 2. Start infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d postgres redis qdrant
```

### 3. Backend

```bash
cd backend/
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp ../.env .env                  # or point to root .env directly

alembic upgrade head             # apply DB migrations
uvicorn app.main:app --reload    # http://localhost:8000
```

API docs: http://localhost:8000/api/docs

### 4. ARQ background worker

In a separate terminal (same virtualenv):

```bash
cd backend/
arq arq_worker.WorkerSettings
```

The worker handles async knowledge indexing jobs queued by the API.

### 5. Frontend

```bash
cd frontend/
npm install
npm run dev                      # http://localhost:3000
```

### 6. WhatsApp microservice (optional)

Only needed if you're using the WhatsApp channel.

```bash
cd services/whatsapp/
npm install
npm run dev                      # http://localhost:3001
```

Requires `REDIS_URL`, `FASTAPI_URL`, and `INTERNAL_SECRET` set in the environment.

---

## Run everything with Docker

To run all services (backend + worker + WhatsApp) in Docker:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Useful commands:

```bash
# Tail backend logs
docker compose -f docker/docker-compose.yml logs -f backend

# Tail worker logs
docker compose -f docker/docker-compose.yml logs -f arq_worker

# Stop all + wipe volumes
docker compose -f docker/docker-compose.yml down -v
```

---

## Testing

```bash
cd backend/

# All tests
python -m pytest

# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# Stop on first failure, verbose
python -m pytest -x -v

# Run a specific test
python -m pytest tests/unit/test_auth_extended_service.py::test_login_returns_tokens
```

---

## Database migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration from model changes
alembic revision --autogenerate -m "describe the change"
```

---

## Services at a glance

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |
| WhatsApp service | http://localhost:3001 |
| Qdrant UI | http://localhost:6333/dashboard |

---

## Docs

See [`docs/`](docs/README.md) for full architecture, feature specs, database schema, business rules, and implementation phases.
