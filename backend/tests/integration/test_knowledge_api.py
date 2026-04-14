"""Integration tests for Knowledge Base API (ARQ-based async indexing)."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.integration.conftest import make_verified_token

AGENTS_BASE = "/api/v1/agents"


async def _get_headers(client, db_engine, email="knowledgeuser@example.com"):
    token = await make_verified_token(client, db_engine, email)
    return {"Authorization": f"Bearer {token}"}


async def _create_agent(client, headers, name="KB Bot"):
    resp = await client.post(AGENTS_BASE, json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _fake_arq():
    """Return a mock ArqRedis that swallows enqueue_job calls."""
    arq = MagicMock()
    arq.enqueue_job = AsyncMock(return_value=None)
    return arq


class TestAddUrl:
    @pytest.mark.anyio
    async def test_add_url_returns_202(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/url",
                json={"root_url": "https://example.com"},
                headers=headers,
            )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 202
        data = resp.json()
        assert data["source_type"] == "url"
        assert data["indexing_status"] == "pending"
        assert data["root_url"] == "https://example.com"

    @pytest.mark.anyio
    async def test_add_url_requires_auth(self, client, db_engine):
        resp = await client.post(
            f"{AGENTS_BASE}/{uuid.uuid4()}/knowledge/url",
            json={"root_url": "https://example.com"},
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_add_url_wrong_agent_returns_403(self, client, db_engine):
        h1 = await _get_headers(client, db_engine, "owner2@example.com")
        h2 = await _get_headers(client, db_engine, "thief2@example.com")
        agent_id = await _create_agent(client, h1)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/url",
                json={"root_url": "https://example.com"},
                headers=h2,
            )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 403


class TestAddText:
    @pytest.mark.anyio
    async def test_add_text_returns_202(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "Company FAQ", "content": "We are open Monday to Friday 9am to 5pm."},
                headers=headers,
            )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 202
        data = resp.json()
        assert data["source_type"] == "text"
        assert data["title"] == "Company FAQ"
        assert data["indexing_status"] == "pending"

    @pytest.mark.anyio
    async def test_add_empty_text_returns_422(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "Empty", "content": "   "},
                headers=headers,
            )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 422


class TestUploadDocument:
    @pytest.mark.anyio
    async def test_upload_txt_returns_202(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            file_bytes = b"Our return policy allows returns within 30 days of purchase."
            with patch("app.services.knowledge_service.TEMP_UPLOAD_DIR", "/tmp"):
                resp = await client.post(
                    f"{AGENTS_BASE}/{agent_id}/knowledge/upload",
                    files={"file": ("policy.txt", io.BytesIO(file_bytes), "text/plain")},
                    headers=headers,
                )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 202
        data = resp.json()
        assert data["source_type"] == "file"
        assert data["file_name"] == "policy.txt"
        assert data["indexing_status"] == "pending"


class TestListKnowledge:
    @pytest.mark.anyio
    async def test_list_empty(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            resp = await client.get(f"{AGENTS_BASE}/{agent_id}/knowledge", headers=headers)
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["data"] == []

    @pytest.mark.anyio
    async def test_list_shows_added_sources(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "FAQ", "content": "We are open Monday to Friday 9am-5pm."},
                headers=headers,
            )
            resp = await client.get(f"{AGENTS_BASE}/{agent_id}/knowledge", headers=headers)
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestDeleteKnowledge:
    @pytest.mark.anyio
    async def test_delete_source(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            add = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "FAQ", "content": "We are open Monday to Friday 9am-5pm."},
                headers=headers,
            )
            source_id = add.json()["id"]

            with patch("app.services.knowledge_service.delete_source_vectors", new_callable=AsyncMock):
                resp = await client.delete(
                    f"{AGENTS_BASE}/{agent_id}/knowledge/{source_id}",
                    headers=headers,
                )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 204

        from app.core.arq_pool import get_arq_pool
        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            list_resp = await client.get(f"{AGENTS_BASE}/{agent_id}/knowledge", headers=headers)
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert list_resp.json()["total"] == 0


class TestGetStatus:
    @pytest.mark.anyio
    async def test_status_returns_pending(self, client, db_engine):
        headers = await _get_headers(client, db_engine)
        agent_id = await _create_agent(client, headers)

        from app.core.arq_pool import get_arq_pool
        from app.main import app

        app.dependency_overrides[get_arq_pool] = lambda: _fake_arq()
        try:
            add = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "FAQ", "content": "We are open Monday to Friday 9am-5pm."},
                headers=headers,
            )
            source_id = add.json()["id"]

            resp = await client.get(
                f"{AGENTS_BASE}/{agent_id}/knowledge/{source_id}/status",
                headers=headers,
            )
        finally:
            app.dependency_overrides.pop(get_arq_pool, None)

        assert resp.status_code == 200
        assert resp.json()["indexing_status"] == "pending"
