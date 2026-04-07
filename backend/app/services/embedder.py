"""Embedder — OpenAI text-embedding-3-small + Qdrant upsert."""

import uuid

from openai import AsyncOpenAI
from qdrant_client.models import PointStruct

from app.core.config import get_settings
from app.core.qdrant import collection_name, ensure_collection, get_qdrant_client

EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100  # OpenAI max per request


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed a list of text chunks using OpenAI. Returns list of float vectors."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    all_embeddings: list[list[float]] = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        response = await client.embeddings.create(model=EMBED_MODEL, input=batch)
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings


async def upsert_chunks(
    agent_id: str,
    source_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    source_type: str = "unknown",
    source_title: str = "",
) -> None:
    """Store chunks + embeddings in Qdrant with metadata."""
    await ensure_collection(agent_id)
    client = get_qdrant_client()
    col = collection_name(agent_id)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "agent_id": agent_id,
                "source_id": source_id,
                "source_type": source_type,
                "source_title": source_title,
                "chunk_index": i,
                "text": chunk,
            },
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    await client.upsert(collection_name=col, points=points)


async def delete_source_vectors(agent_id: str, source_id: str) -> None:
    """Delete all vectors for a specific source from Qdrant."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = get_qdrant_client()
    col = collection_name(agent_id)
    exists = await client.collection_exists(col)
    if not exists:
        return

    await client.delete(
        collection_name=col,
        points_selector=Filter(
            must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]
        ),
    )
