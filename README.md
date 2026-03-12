# Botlixio v2

**AI Agent Builder SaaS** — Build, configure, and deploy custom AI chatbot agents across multiple channels.

## Quick Start (Development)

### 1. Start infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 2. Backend

```bash
cd backend/
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env             # Fill in your values
alembic upgrade head             # Apply DB migrations
uvicorn app.main:app --reload    # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend/
npm install
npm run dev                      # http://localhost:3000
```

## Commands

```bash
# Run tests
cd backend && python -m pytest

# Run only unit tests
python -m pytest tests/unit/

# API docs
open http://localhost:8000/api/docs
```

## Docs

See [`docs/`](docs/README.md) for full architecture, feature specs, and implementation phases.
