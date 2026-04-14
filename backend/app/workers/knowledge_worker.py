"""
ARQ background jobs for knowledge base indexing.

Job flow per source type:
  URL  → crawl pages → chunk → embed → upsert Qdrant → INDEXED
  FILE → read temp file → parse → chunk → embed → upsert Qdrant → INDEXED
  TEXT → chunk → embed → upsert Qdrant → INDEXED (fast, but still async for consistency)

Status transitions:
  PENDING → PROCESSING → INDEXED
  PENDING → PROCESSING → FAILED (on any exception)
"""

import hashlib
import os
import uuid

from app.core.database import get_session_factory
from app.models.enums import IndexingStatus, KnowledgeSourceType
from app.repositories.knowledge_repo import KnowledgeRepository
from app.services.chunker import chunk_text
from app.services.crawler import crawl_url
from app.services.document_parser import parse_document
from app.services.embedder import delete_source_vectors, embed_chunks, upsert_chunks

MAX_CHAR_COUNT = 100_000
TEMP_UPLOAD_DIR = "/tmp/botlixio_uploads"


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ─── URL indexing ────────────────────────────────────────────────────────────

async def index_url_source(
    ctx: dict,
    *,
    knowledge_id: str,
    root_url: str,
    path_filter: str | None,
    max_pages: int,
    agent_id: str,
) -> None:
    """Crawl root_url (respecting path_filter up to max_pages), chunk, embed, store."""
    async with get_session_factory()() as db:
        repo = KnowledgeRepository(db)
        item = await repo.get_by_id(uuid.UUID(knowledge_id))
        if item is None:
            return  # deleted before the job ran

        await repo.update_status(item, IndexingStatus.PROCESSING)
        await db.commit()

        try:
            combined_text, pages = await crawl_url(
                root_url, max_pages=max_pages, path_filter=path_filter
            )
            combined_text = combined_text[:MAX_CHAR_COUNT]

            chunks = chunk_text(combined_text)
            embeddings = await embed_chunks(chunks)

            await upsert_chunks(
                agent_id=agent_id,
                source_id=knowledge_id,
                chunks=chunks,
                embeddings=embeddings,
                source_type="url",
                source_title=root_url,
            )

            await repo.update_status(
                item,
                IndexingStatus.INDEXED,
                chunk_count=len(chunks),
                content=combined_text,
                content_hash=_content_hash(combined_text),
                crawled_pages=[
                    {"url": p.url, "title": p.title, "char_count": p.char_count}
                    for p in pages
                ],
            )
            await db.commit()

        except Exception as exc:
            await repo.update_status(
                item, IndexingStatus.FAILED, error_message=str(exc)[:500]
            )
            await db.commit()
            raise


# ─── Single-page add (append to existing URL source) ─────────────────────────

async def index_single_page(
    ctx: dict,
    *,
    knowledge_id: str,
    page_url: str,
    agent_id: str,
) -> None:
    """Scrape one URL and append it to an existing URL-type knowledge source."""
    async with get_session_factory()() as db:
        repo = KnowledgeRepository(db)
        item = await repo.get_by_id(uuid.UUID(knowledge_id))
        if item is None:
            return

        try:
            combined_text, pages = await crawl_url(page_url, max_pages=1)
            if not pages:
                return

            page = pages[0]
            text = combined_text[:MAX_CHAR_COUNT]
            chunks = chunk_text(text)
            embeddings = await embed_chunks(chunks)

            # Upsert with a sub-source ID so we can delete just this page later
            page_source_id = f"{knowledge_id}::{page_url}"
            await upsert_chunks(
                agent_id=agent_id,
                source_id=page_source_id,
                chunks=chunks,
                embeddings=embeddings,
                source_type="url",
                source_title=page.title,
            )

            await repo.append_crawled_page(
                item,
                {"url": page.url, "title": page.title, "char_count": page.char_count},
            )
            await db.commit()

        except Exception as exc:
            # Don't fail the whole source — just log
            print(f"[knowledge_worker] index_single_page failed for {page_url}: {exc}")


# ─── File indexing ───────────────────────────────────────────────────────────

async def index_file_source(
    ctx: dict,
    *,
    knowledge_id: str,
    agent_id: str,
    filename: str,
) -> None:
    """Read a saved temp file, parse, chunk, embed, store."""
    async with get_session_factory()() as db:
        repo = KnowledgeRepository(db)
        item = await repo.get_by_id(uuid.UUID(knowledge_id))
        if item is None:
            return

        await repo.update_status(item, IndexingStatus.PROCESSING)
        await db.commit()

        temp_path = os.path.join(TEMP_UPLOAD_DIR, knowledge_id)

        try:
            with open(temp_path, "rb") as f:
                file_bytes = f.read()

            text = parse_document(filename, file_bytes)
            if not text.strip():
                raise ValueError("Could not extract any text from the file.")

            text = text[:MAX_CHAR_COUNT]
            chunks = chunk_text(text)
            embeddings = await embed_chunks(chunks)

            await upsert_chunks(
                agent_id=agent_id,
                source_id=knowledge_id,
                chunks=chunks,
                embeddings=embeddings,
                source_type="file",
                source_title=filename,
            )

            await repo.update_status(
                item,
                IndexingStatus.INDEXED,
                chunk_count=len(chunks),
                content=text,
                content_hash=_content_hash(text),
            )
            await db.commit()

        except Exception as exc:
            await repo.update_status(
                item, IndexingStatus.FAILED, error_message=str(exc)[:500]
            )
            await db.commit()
            raise

        finally:
            # Clean up temp file regardless of success/failure
            if os.path.exists(temp_path):
                os.remove(temp_path)


# ─── Text indexing ───────────────────────────────────────────────────────────

async def index_text_source(
    ctx: dict,
    *,
    knowledge_id: str,
    agent_id: str,
    text: str,
) -> None:
    """Chunk and embed a raw text source."""
    async with get_session_factory()() as db:
        repo = KnowledgeRepository(db)
        item = await repo.get_by_id(uuid.UUID(knowledge_id))
        if item is None:
            return

        await repo.update_status(item, IndexingStatus.PROCESSING)
        await db.commit()

        try:
            chunks = chunk_text(text)
            embeddings = await embed_chunks(chunks)

            await upsert_chunks(
                agent_id=agent_id,
                source_id=knowledge_id,
                chunks=chunks,
                embeddings=embeddings,
                source_type="text",
                source_title=item.title,
            )

            await repo.update_status(
                item,
                IndexingStatus.INDEXED,
                chunk_count=len(chunks),
                content_hash=_content_hash(text),
            )
            await db.commit()

        except Exception as exc:
            await repo.update_status(
                item, IndexingStatus.FAILED, error_message=str(exc)[:500]
            )
            await db.commit()
            raise


# ─── Vector cleanup ──────────────────────────────────────────────────────────

async def remove_source_vectors(
    ctx: dict,
    *,
    agent_id: str,
    source_id: str,
) -> None:
    """Delete all Qdrant vectors for a source. Used when a source is deleted."""
    await delete_source_vectors(agent_id, source_id)


# ─── Job function list (referenced in WorkerSettings) ────────────────────────

KNOWLEDGE_JOBS = [
    index_url_source,
    index_single_page,
    index_file_source,
    index_text_source,
    remove_source_vectors,
]
