"""
Botlixio — Async database engine, session factory, and Base.

Provides:
  - ``Base`` — declarative base for all SQLAlchemy models
  - ``get_engine`` — lazily builds the async engine from DATABASE_URL
  - ``get_session_factory`` — lazily builds an ``AsyncSession`` factory
  - ``get_db`` — FastAPI dependency that yields a session per request
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy 2.0 models."""

    pass


@lru_cache
def get_engine() -> AsyncEngine:
    """Create the async engine on first use."""
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create the async session factory on first use."""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields an async session and closes it after use.

    Usage::

        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
