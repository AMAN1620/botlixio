"""Retriever — embed query + search Qdrant for relevant chunks."""

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.qdrant import collection_name, get_qdrant_client

EMBED_MODEL = "text-embedding-3-small"
MIN_SCORE = 0.35  # discard low-relevance chunks


async def retrieve(
    agent_id: str, query: str, top_k: int = 5
) -> list[dict]:
    """
    Embed the query and return the top_k most relevant chunks from Qdrant.

    Returns list of dicts: {"text": str, "source_title": str, "source_type": str, "score": float}
    Returns empty list if collection doesn't exist, no results, or all below MIN_SCORE.
    """
    settings = get_settings()
    client = get_qdrant_client()
    col = collection_name(agent_id)

    exists = await client.collection_exists(col)
    if not exists:
        return []

    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await openai_client.embeddings.create(model=EMBED_MODEL, input=[query])
    query_vector = response.data[0].embedding

    results = await client.query_points(
        collection_name=col,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        score_threshold=MIN_SCORE,
    )

    chunks = []
    for point in results.points:
        if not point.payload:
            continue
        chunks.append({
            "text": point.payload.get("text", ""),
            "source_title": point.payload.get("source_title", "Unknown"),
            "source_type": point.payload.get("source_type", "unknown"),
            "score": round(point.score, 3),
        })

    return chunks
