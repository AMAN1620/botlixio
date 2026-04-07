"""Knowledge service — orchestrates ingestion: crawl/parse → chunk → embed → store."""

import uuid

from fastapi import HTTPException, status, UploadFile

from app.models.enums import KnowledgeSourceType
from app.models.knowledge import AgentKnowledge
from app.repositories.knowledge_repo import KnowledgeRepository
from app.services.chunker import chunk_text
from app.services.crawler import crawl_url
from app.services.document_parser import parse_document
from app.services.embedder import delete_source_vectors, embed_chunks, upsert_chunks

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_CHAR_COUNT = 100_000


async def _embed_or_raise(chunks: list[str]) -> list[list[float]]:
    """Wrap embed_chunks with a clear user-facing error."""
    try:
        return await embed_chunks(chunks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding failed — check your OPENAI_API_KEY and project model permissions: {e}",
        )


class KnowledgeService:
    def __init__(self, repo: KnowledgeRepository) -> None:
        self._repo = repo

    async def add_url(self, *, agent_id: uuid.UUID, url: str) -> AgentKnowledge:
        """Crawl a URL, chunk content, embed, store in Qdrant + DB."""
        try:
            text = await crawl_url(url)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

        text = text[:MAX_CHAR_COUNT]
        chunks = chunk_text(text)
        embeddings = await _embed_or_raise(chunks)

        item = await self._repo.create(
            agent_id=agent_id,
            source_type=KnowledgeSourceType.URL,
            title=url,
            content=text,
            chunk_count=len(chunks),
        )

        await upsert_chunks(
            agent_id=str(agent_id),
            source_id=str(item.id),
            chunks=chunks,
            embeddings=embeddings,
            source_type="url",
            source_title=url,
        )

        return item

    async def add_document(self, *, agent_id: uuid.UUID, file: UploadFile) -> AgentKnowledge:
        """Parse an uploaded file, chunk, embed, store."""
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds 10 MB limit",
            )

        filename = file.filename or "document"
        text = parse_document(filename, content)
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from file",
            )

        text = text[:MAX_CHAR_COUNT]
        chunks = chunk_text(text)
        embeddings = await _embed_or_raise(chunks)

        item = await self._repo.create(
            agent_id=agent_id,
            source_type=KnowledgeSourceType.FILE,
            title=filename,
            content=text,
            file_name=filename,
            file_size=len(content),
            chunk_count=len(chunks),
        )

        await upsert_chunks(
            agent_id=str(agent_id),
            source_id=str(item.id),
            chunks=chunks,
            embeddings=embeddings,
            source_type="file",
            source_title=filename,
        )

        return item

    async def add_text(self, *, agent_id: uuid.UUID, title: str, content: str) -> AgentKnowledge:
        """Ingest raw text content."""
        if not content.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Content cannot be empty",
            )

        content = content[:MAX_CHAR_COUNT]
        chunks = chunk_text(content)
        embeddings = await _embed_or_raise(chunks)

        item = await self._repo.create(
            agent_id=agent_id,
            source_type=KnowledgeSourceType.TEXT,
            title=title,
            content=content,
            chunk_count=len(chunks),
        )

        await upsert_chunks(
            agent_id=str(agent_id),
            source_id=str(item.id),
            chunks=chunks,
            embeddings=embeddings,
            source_type="text",
            source_title=title,
        )

        return item

    async def list_sources(self, *, agent_id: uuid.UUID) -> list[AgentKnowledge]:
        return await self._repo.get_by_agent(agent_id)

    async def delete_source(self, *, source_id: uuid.UUID, agent_id: uuid.UUID) -> None:
        item = await self._repo.get_by_id(source_id)
        if item is None or item.agent_id != agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

        await delete_source_vectors(str(agent_id), str(source_id))
        await self._repo.delete(item)
