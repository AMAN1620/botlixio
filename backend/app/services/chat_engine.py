"""Chat engine — RAG pipeline: session → history → retrieve → LLM → save."""

import time
import uuid

from app.models.agent import Agent
from app.models.enums import AgentStatus
from app.repositories.chat_repo import ChatRepository
from app.services.llm_client import chat_completion
from app.services.retriever import retrieve

HISTORY_LIMIT = 10
CONTEXT_CHUNKS = 5

_NO_CONTEXT_REPLY = (
    "I can only answer questions based on the knowledge base I've been given. "
    "I don't have information about that topic. "
    "Please ask something related to the content I was trained on."
)

_STRICT_SYSTEM_SUFFIX = """
STRICT INSTRUCTIONS — follow these exactly:
1. Answer ONLY using the knowledge base context provided above.
2. If the answer is not found in the context, reply with exactly:
   "I don't have information about that in my knowledge base. Please ask something related to the provided content."
3. Do NOT use any external knowledge, general knowledge, or assumptions.
4. Do NOT make up information.
5. Be concise and cite which source you used when possible.
"""


def _build_context_block(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] Source: {chunk['source_title']}\n{chunk['text']}")
    return "\n\n".join(lines)


def _deduplicated_sources(chunks: list[dict]) -> list[str]:
    """Return unique source titles preserving order."""
    seen = set()
    sources = []
    for chunk in chunks:
        title = chunk["source_title"]
        if title not in seen:
            seen.add(title)
            sources.append(title)
    return sources


async def process_message(
    *,
    agent: Agent,
    session_identifier: str,
    user_message: str,
    chat_repo: ChatRepository,
) -> dict:
    """
    Full RAG chat pipeline.

    Returns: {"reply": str, "session_id": str, "sources": list[str]}
    """
    # 1. Agent must be LIVE
    if agent.status != AgentStatus.LIVE:
        return {
            "reply": agent.fallback_message or "This agent is not currently available.",
            "session_id": session_identifier,
            "sources": [],
        }

    # 2. Get or create session
    session = await chat_repo.get_or_create_session(
        agent_id=agent.id,
        session_identifier=session_identifier,
    )

    # 3. Load recent history
    history = await chat_repo.get_recent_messages(session_id=session.id, limit=HISTORY_LIMIT)

    # 4. Retrieve relevant knowledge chunks
    chunks = await retrieve(str(agent.id), user_message, top_k=CONTEXT_CHUNKS)

    # 5. Build system prompt — strict grounding
    base_prompt = agent.system_prompt or "You are a helpful customer support assistant."

    if chunks:
        context_block = _build_context_block(chunks)
        system_prompt = (
            f"{base_prompt}\n\n"
            f"KNOWLEDGE BASE CONTEXT:\n{context_block}"
            f"{_STRICT_SYSTEM_SUFFIX}"
        )
    else:
        # No relevant chunks found — instruct to decline
        system_prompt = (
            f"{base_prompt}\n\n"
            "No relevant context was found in the knowledge base for this query.\n"
            + _STRICT_SYSTEM_SUFFIX
        )

    # 6. Build message list
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    # 7. Save user message
    await chat_repo.add_message(session_id=session.id, role="user", content=user_message)

    # 8. If no chunks at all, skip LLM call and return the no-context reply directly
    if not chunks:
        await chat_repo.add_message(
            session_id=session.id,
            role="assistant",
            content=_NO_CONTEXT_REPLY,
            response_time_ms=0,
        )
        return {
            "reply": _NO_CONTEXT_REPLY,
            "session_id": str(session.id),
            "sources": [],
        }

    # 9. Call LLM
    start = time.monotonic()
    reply = await chat_completion(
        messages=messages,
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # 10. Save assistant message
    await chat_repo.add_message(
        session_id=session.id,
        role="assistant",
        content=reply,
        response_time_ms=elapsed_ms,
    )

    return {
        "reply": reply,
        "session_id": str(session.id),
        "sources": _deduplicated_sources(chunks),
    }
