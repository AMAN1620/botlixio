"""ARQ Redis pool — shared across the FastAPI app for enqueuing jobs."""

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from app.core.config import get_settings

_pool: ArqRedis | None = None


def _redis_settings() -> RedisSettings:
    settings = get_settings()
    # arq expects host/port separately — parse from REDIS_URL
    # e.g. redis://localhost:6379  or  redis://redis:6379
    url = settings.REDIS_URL
    url = url.replace("redis://", "")
    host, _, rest = url.partition(":")
    # rest may be "6379" or "6379/0" — strip optional /db suffix
    port_str = rest.split("/")[0] if rest else "6379"
    port = int(port_str) if port_str else 6379
    return RedisSettings(host=host, port=port)


async def get_arq_pool() -> ArqRedis:
    """Return (and lazily create) the shared ARQ Redis pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(_redis_settings())
    return _pool


async def close_arq_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
