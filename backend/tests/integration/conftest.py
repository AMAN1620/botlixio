"""
Integration test fixtures.

Each test gets a fresh DB schema (drop+create) and an httpx client
where get_db yields a new committed session per request.
This allows multi-request tests (e.g. register then login) to see each other's data.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return get_settings().DATABASE_URL


@pytest_asyncio.fixture(scope="function")
async def client(test_db_url):
    """
    Provide an httpx client with a clean DB per test function.

    Each HTTP request to the app gets its own session + commit cycle,
    so data written by one request is visible to subsequent requests
    in the same test.
    """
    engine = create_async_engine(test_db_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=True
    )

    # Fresh tables for this test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def _override_get_db():
        """New session per request — commits on success, rolls back on error."""
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
