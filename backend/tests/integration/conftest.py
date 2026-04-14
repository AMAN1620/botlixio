"""
Integration test fixtures.

Each test gets a fresh DB schema (drop+create) and an httpx client
where get_db yields a new committed session per request.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return get_settings().DATABASE_URL


@pytest_asyncio.fixture(scope="function")
async def db_engine(test_db_url):
    """Async engine with a fresh schema per test function."""
    engine = create_async_engine(test_db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_engine):
    """
    httpx AsyncClient wired to the test DB.
    Each HTTP request gets its own session + commit cycle.
    """
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=True
    )

    async def _override_get_db():
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


async def make_verified_token(
    client: AsyncClient,
    engine,
    email: str,
    password: str = "password123",
    full_name: str = "Test User",
) -> str:
    """
    Register a user, force-verify them in the DB, and return an access token.
    Bypasses the email verification flow for integration tests.
    """
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET is_verified = TRUE WHERE email = :email"),
            {"email": email},
        )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()["access_token"]
