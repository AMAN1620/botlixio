# Pydantic Settings — Configuration Management

> **What is this?** Pydantic Settings is a library that reads your `.env` file and environment variables, validates them, converts their types, and gives you a fully typed Python object. It catches misconfiguration at app startup — not when a user first hits your API.

---

## Key Concepts

### The Problem

Without pydantic-settings, you'd read env vars manually:

```python
# ❌ Fragile — no validation, everything is a string
import os
db_url = os.getenv("DATABASE_URL")           # Could be None!
token_expiry = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")  # Returns "30" (string, not int)
```

With pydantic-settings, you declare what you need with types, and it does the rest:

```python
# ✅ Validated, typed, with defaults
class Settings(BaseSettings):
    DATABASE_URL: str              # Required — startup fails if missing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30   # Optional — defaults to 30
```

### How It Works

```
.env file → Pydantic Settings → Python object with validated, typed fields
                    ↑
            Also reads OS env vars
            (.env values take precedence over os.environ)
```

### Required vs Optional

```python
DATABASE_URL: str        # Required — NO default — startup CRASHES if missing
SECRET_KEY: str          # Required — same

OPENAI_API_KEY: str = "" # Optional — has default — startup succeeds without it
DEBUG: bool = False      # Optional — auto-converts "true"/"false" strings to bool
```

---

## Code Examples

### Our Settings class (`backend/app/core/config.py`)

```python
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",          # ← reads this file automatically
        env_file_encoding="utf-8",
        extra="ignore",           # ← doesn't crash on unknown env vars
    )

    # Required (no default = crash if missing)
    DATABASE_URL: str
    SECRET_KEY: str
    REDIS_URL: str

    # Optional (has defaults)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30    # ← "30" in .env → int 30
    DEBUG: bool = False                       # ← "true" in .env → bool True

    # Computed property
    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse "http://a.com,http://b.com" → ["http://a.com", "http://b.com"]"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
```

**What this does line by line:**
- `SettingsConfigDict(env_file=".env")` — automatically load from `.env`
- `extra="ignore"` — if `.env` has vars not in our class, don't crash
- `DATABASE_URL: str` — required, no default → `ValidationError` if missing
- `ACCESS_TOKEN_EXPIRE_MINUTES: int = 30` — reads string "60" from env, converts to `int(60)`
- `@computed_field` — a property that shows up in the object but is calculated, not from env

### Singleton pattern with `lru_cache`

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Usage everywhere:
settings = get_settings()  # ← always returns the SAME instance
```

**Why?** Without `lru_cache`, every call re-reads `.env` and re-validates. With it, Settings is created once and reused. Like a global, but cleaner.

---

## How we test it (`tests/unit/test_config.py`)

```python
from unittest.mock import patch
import os

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
    "SECRET_KEY": "a" * 64,
    "REDIS_URL": "redis://localhost:6379/0",
}

class TestMissingRequiredVars:
    def test_missing_database_url_raises(self):
        env = {**REQUIRED_ENV}
        env.pop("DATABASE_URL")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            with pytest.raises(Exception):  # ValidationError
                Settings()
```

**Pattern:** `patch.dict(os.environ, ..., clear=True)` replaces ALL env vars with exactly what you specify. This isolates each test from your actual `.env`.

---

## Commands

```bash
# Test config loading
cd backend/
python -m pytest tests/unit/test_config.py -v

# Quick check settings load correctly
python -c "from app.core.config import get_settings; s = get_settings(); print(s.DATABASE_URL)"
```

---

## Gotchas & Tips

- **`clear=True` in `patch.dict`** — if you don't set this, your real `.env` values leak into tests. Always use `clear=True` for config tests.
- **Type coercion is automatic** — `"30"` → `int(30)`, `"true"` → `bool(True)`. You don't need to cast manually.
- **`extra="ignore"` is important** — without it, any unknown variable in `.env` causes a `ValidationError`. Your `.env` might have vars for other services.
- **Order of precedence:** OS env vars > `.env` file > default values. This means Docker container env vars override `.env`.
- **`lru_cache` warning:** If you modify `.env` during a running app, Settings won't update. Restart the server.

---

## See Also

- [environment-variables.md](environment-variables.md) — the `.env` file this reads from
- [sqlalchemy-async.md](sqlalchemy-async.md) — uses `settings.DATABASE_URL`
- [testing-fastapi.md](testing-fastapi.md) — uses `patch.dict` pattern from here
