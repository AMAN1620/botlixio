"""Qdrant vector DB client and collection helpers."""

from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings

EMBEDDING_DIM = 1536  # text-embedding-3-small


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.QDRANT_URL)


def collection_name(agent_id: str) -> str:
    settings = get_settings()
    return f"{settings.QDRANT_COLLECTION_PREFIX}_{agent_id}"


async def ensure_collection(agent_id: str) -> None:
    """Create Qdrant collection for agent if it doesn't exist."""
    client = get_qdrant_client()
    name = collection_name(agent_id)
    exists = await client.collection_exists(name)
    if not exists:
        await client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


async def delete_collection(agent_id: str) -> None:
    """Delete the entire Qdrant collection for an agent."""
    client = get_qdrant_client()
    name = collection_name(agent_id)
    exists = await client.collection_exists(name)
    if exists:
        await client.delete_collection(name)
