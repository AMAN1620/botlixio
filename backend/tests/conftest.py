"""
Shared pytest fixtures for Botlixio backend tests.

Fixtures added here are available to all test modules automatically.
Phase-specific fixtures (db session, auth client, etc.) will be added
as those phases are implemented.
"""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio as the async backend for pytest-asyncio."""
    return "asyncio"
