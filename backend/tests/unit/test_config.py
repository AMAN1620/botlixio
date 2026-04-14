"""
Tests for app.core.config — Pydantic Settings.

TDD RED phase: These tests are written BEFORE the implementation.
They verify:
  - Settings load from environment variables
  - Required variables are validated (missing vars raise errors)
  - Type coercion works correctly (str → int, str → bool, etc.)
  - Default values are applied when optional vars are absent
  - CORS_ORIGINS is parsed as a list
"""

import os
from unittest.mock import patch

import pytest


# ---------- Helpers ---------- #

# Minimal required env vars for Settings to instantiate
REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
    "SECRET_KEY": "a" * 64,
    "REDIS_URL": "redis://localhost:6379/0",
}


def _make_env(**overrides: str) -> dict[str, str]:
    """Return a copy of REQUIRED_ENV merged with overrides."""
    env = {**REQUIRED_ENV, **overrides}
    return env


# ---------- Loading from env ---------- #


class TestSettingsLoading:
    """Settings should load values from environment variables."""

    def test_loads_database_url(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert str(settings.DATABASE_URL) == REQUIRED_ENV["DATABASE_URL"]

    def test_loads_secret_key(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.SECRET_KEY == REQUIRED_ENV["SECRET_KEY"]

    def test_loads_redis_url(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert str(settings.REDIS_URL) == REQUIRED_ENV["REDIS_URL"]


# ---------- Missing required vars ---------- #


class TestMissingRequiredVars:
    """Settings must reject instantiation when required vars are absent."""

    def test_missing_database_url_raises(self) -> None:
        env = _make_env()
        env.pop("DATABASE_URL")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(Exception):  # ValidationError
                Settings(_env_file=None)

    def test_missing_secret_key_raises(self) -> None:
        env = _make_env()
        env.pop("SECRET_KEY")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(Exception):
                Settings(_env_file=None)

    def test_missing_redis_url_raises(self) -> None:
        env = _make_env()
        env.pop("REDIS_URL")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(Exception):
                Settings(_env_file=None)


# ---------- Type coercion ---------- #


class TestTypeCoercion:
    """Environment values are strings; Settings should coerce them."""

    def test_access_token_expire_minutes_coerced_to_int(self) -> None:
        with patch.dict(os.environ, _make_env(ACCESS_TOKEN_EXPIRE_MINUTES="60"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
            assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)

    def test_refresh_token_expire_days_coerced_to_int(self) -> None:
        with patch.dict(os.environ, _make_env(REFRESH_TOKEN_EXPIRE_DAYS="14"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 14
            assert isinstance(settings.REFRESH_TOKEN_EXPIRE_DAYS, int)

    def test_debug_coerced_to_bool(self) -> None:
        with patch.dict(os.environ, _make_env(DEBUG="true"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.DEBUG is True

    def test_debug_false_string(self) -> None:
        with patch.dict(os.environ, _make_env(DEBUG="false"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.DEBUG is False


# ---------- Default values ---------- #


class TestDefaultValues:
    """Optional vars should use sensible defaults when absent from env."""

    def test_algorithm_default(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.ALGORITHM == "HS256"

    def test_access_token_expire_default(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_refresh_token_expire_default(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_debug_default_false(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings(_env_file=None)
            assert settings.DEBUG is False

    def test_environment_default(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.ENVIRONMENT == "development"

    def test_email_from_default(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings(_env_file=None)
            assert settings.EMAIL_FROM == "noreply@botlixio.com"


# ---------- CORS origins parsing ---------- #


class TestCORSOrigins:
    """CORS_ORIGINS should be parsed as a list of strings."""

    def test_single_origin(self) -> None:
        with patch.dict(os.environ, _make_env(CORS_ORIGINS="http://localhost:3000"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert isinstance(settings.cors_origins_list, list)
            assert "http://localhost:3000" in settings.cors_origins_list

    def test_multiple_origins(self) -> None:
        origins = "http://localhost:3000,https://botlixio.com,https://app.botlixio.com"
        with patch.dict(os.environ, _make_env(CORS_ORIGINS=origins), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert len(settings.cors_origins_list) == 3
            assert "https://botlixio.com" in settings.cors_origins_list

    def test_empty_cors_origins_default(self) -> None:
        with patch.dict(os.environ, _make_env(), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert isinstance(settings.cors_origins_list, list)


# ---------- Computed / derived properties ---------- #


class TestDerivedProperties:
    """Settings may expose computed helpers."""

    def test_is_production(self) -> None:
        with patch.dict(os.environ, _make_env(ENVIRONMENT="production"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.is_production is True

    def test_is_not_production(self) -> None:
        with patch.dict(os.environ, _make_env(ENVIRONMENT="development"), clear=True):
            from app.core.config import Settings

            settings = Settings()
            assert settings.is_production is False
