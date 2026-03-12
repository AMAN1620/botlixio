# Environment Variables & .env Files

> **What is this?** Environment variables are named values (like passwords and API keys) that live outside your code. They let you configure an application differently for development, staging, and production without changing any code.

---

## Key Concepts

### Why not hardcode secrets?

```python
# ❌ BAD — hardcoded in code
DATABASE_URL = "postgresql://user:mypassword@localhost/db"

# ✅ GOOD — read from environment
import os
DATABASE_URL = os.getenv("DATABASE_URL")
```

If you hardcode secrets and push to GitHub, anyone can see them. Environment variables stay on the machine, not in the repo.

### The `.env` Workflow

```
.env.example   → committed to Git (safe — no real secrets, just variable names)
.env           → NOT committed (add to .gitignore) — has your actual secrets
```

Developers copy `.env.example` to `.env` and fill in real values locally.

---

## Code Examples

### Our `.env.example` (safe to commit)

```bash
# Database
DATABASE_URL="postgresql+asyncpg://botlixio:botlixio@localhost:5432/botlixio"

# Auth — generate with: openssl rand -hex 32
SECRET_KEY=""

# LLM
OPENAI_API_KEY=""

# Redis
REDIS_URL="redis://localhost:6379/0"

# Frontend
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

Values that are empty (`""`) need to be filled in. Values that already have a dev default can be used as-is.

### Generating secret keys

```bash
# Generate a secure SECRET_KEY
openssl rand -hex 32
# Output: a82f4c91... (32 random bytes in hex = 64 characters)

# Generate a Fernet encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Reading in Python (Phase 1 — pydantic-settings)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    OPENAI_API_KEY: str = ""  # optional, has default

    class Config:
        env_file = ".env"

settings = Settings()  # ← automatically reads .env
```

---

## Commands

```bash
# Copy the example to create your local .env
cp backend/.env.example backend/.env

# Verify a variable is loaded (after activating venv + loading .env)
python3 -c "import os; print(os.getenv('DATABASE_URL'))"
```

---

## Variable Naming Conventions

| Prefix | Meaning |
|--------|---------|
| `DATABASE_*` | Database connection settings |
| `SECRET_*` | Secret keys — NEVER share these |
| `STRIPE_*` | Stripe payment API keys |
| `RESEND_*` | Email service keys |
| `NEXT_PUBLIC_*` | Safe in frontend (exposed to browser — don't put secrets here!) |
| `REDIS_*` | Redis connection config |

**NEXT_PUBLIC_ warning:** In Next.js, any variable starting with `NEXT_PUBLIC_` is embedded in the client-side bundle and visible to anyone. Never put API keys there.

---

## Gotchas & Tips

- **Never commit `.env`** — it's in `.gitignore`. If you accidentally do, rotate your keys immediately.
- **`.env.example` should have the right format but empty/fake values** — it's documentation.
- **Variables without quotes also work** — `SECRET_KEY=abc123` (no quotes) is valid `.env` syntax.
- **Restart the server after changing `.env`** — environment variables are loaded at startup, not dynamically.
- **Each service has its own `.env`** — the backend reads from `backend/.env`. Next.js reads from `frontend/.env.local`.

---

## See Also

- [python-packaging.md](python-packaging.md) — pyproject.toml where pydantic-settings is listed as a dependency
- [docker-basics.md](docker-basics.md) — the database running at the DATABASE_URL
- `docs/tech-stack.md` — full list of all environment variables
