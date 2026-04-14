"""
Botlixio — Application configuration via Pydantic Settings.

Loads all environment variables from `.env`, validates required values,
and provides typed access with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """
    Application settings populated from environment variables.

    Required vars (no default → startup fails if missing):
      - DATABASE_URL
      - SECRET_KEY
      - REDIS_URL

    All other vars have sensible defaults for local development.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown env vars
    )

    # ── Database ──────────────────────────────────
    DATABASE_URL: str

    # ── Auth / JWT ────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── LLM API Keys (optional — admin-configured) ──
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # ── Stripe ────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # ── Email (SMTP) ──────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@botlixio.com"

    # ── OAuth (Google) ─────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # ── Frontend ───────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Redis ─────────────────────────────────────
    REDIS_URL: str

    # ── Qdrant (vector DB) ────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_PREFIX: str = "agent"

    # ── Integration Encryption ────────────────────
    FERNET_KEY: str = ""

    # ── CORS ──────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── App ───────────────────────────────────────
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Computed properties ───────────────────────

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS_ORIGINS into a list."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        """Check if the app is running in production."""
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached singleton for Settings.

    Use this function (instead of ``Settings()``) throughout the app
    so the env is parsed only once.
    """
    return Settings()
