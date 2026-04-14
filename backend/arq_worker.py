"""
ARQ worker entry point.

Run with:
    arq arq_worker.WorkerSettings

Or via Docker:
    command: arq arq_worker.WorkerSettings
"""

import os

from arq.connections import RedisSettings

from app.workers.knowledge_worker import KNOWLEDGE_JOBS


def _redis_settings() -> RedisSettings:
    url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    url = url.replace("redis://", "")
    host, _, rest = url.partition(":")
    port_str = rest.split("/")[0] if rest else "6379"
    port = int(port_str) if port_str else 6379
    return RedisSettings(host=host, port=port)


class WorkerSettings:
    """ARQ WorkerSettings — registers all background jobs."""

    functions = KNOWLEDGE_JOBS
    redis_settings = _redis_settings()

    # How long a job can run before being cancelled (10 min for large crawls)
    job_timeout = 600

    # Retry failed jobs once after 30s
    max_tries = 2
    retry_jobs = True
    keep_result = 300  # keep job result in Redis for 5 min (for polling)
