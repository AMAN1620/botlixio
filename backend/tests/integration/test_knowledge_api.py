"""Integration tests for Knowledge Base API — mocking Crawl4AI + OpenAI."""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest

AGENTS_BASE = "/api/v1/agents"


async def _register_and_get_headers(client, email="knowledgeuser@example.com"):
    await client.post("/api/v1/auth/register", json={
        "email": email, "password": "password123", "full_name": "Knowledge User"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "password123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_agent(client, headers, name="KB Bot"):
    resp = await client.post(AGENTS_BASE, json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _mock_embed_and_upsert():
    """Return a context manager that mocks embed_chunks and upsert_chunks."""
    fake_embeddings = [[0.1] * 1536]
    return (
        patch("app.services.knowledge_service.embed_chunks", new_callable=AsyncMock, return_value=fake_embeddings),
        patch("app.services.knowledge_service.upsert_chunks", new_callable=AsyncMock),
        patch("app.services.knowledge_service.delete_source_vectors", new_callable=AsyncMock),
    )


class TestAddUrl:
    @pytest.mark.anyio
    async def test_add_url_returns_201(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        embed_mock, upsert_mock, _ = _mock_embed_and_upsert()
        with embed_mock, upsert_mock:
            with patch("app.services.knowledge_service.crawl_url", new_callable=AsyncMock,
                       return_value="This is the scraped website content about our services."):
                resp = await client.post(
                    f"{AGENTS_BASE}/{agent_id}/knowledge/url",
                    json={"url": "https://example.com"},
                    headers=headers,
                )

        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "url"
        assert data["title"] == "https://example.com"
        assert data["chunk_count"] >= 1

    @pytest.mark.anyio
    async def test_add_url_crawl_failure_returns_422(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        with patch("app.services.knowledge_service.crawl_url", new_callable=AsyncMock,
                   side_effect=ValueError("Failed to crawl")):
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/url",
                json={"url": "https://broken.example.com"},
                headers=headers,
            )

        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_add_url_requires_auth(self, client):
        resp = await client.post(
            f"{AGENTS_BASE}/{uuid.uuid4()}/knowledge/url",
            json={"url": "https://example.com"},
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_add_url_wrong_agent_returns_403(self, client):
        h1 = await _register_and_get_headers(client, "owner2@example.com")
        h2 = await _register_and_get_headers(client, "thief2@example.com")
        agent_id = await _create_agent(client, h1)

        resp = await client.post(
            f"{AGENTS_BASE}/{agent_id}/knowledge/url",
            json={"url": "https://example.com"},
            headers=h2,
        )
        assert resp.status_code == 403


class TestAddText:
    @pytest.mark.anyio
    async def test_add_text_returns_201(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        embed_mock, upsert_mock, _ = _mock_embed_and_upsert()
        with embed_mock, upsert_mock:
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "Company FAQ", "content": "We are open Monday to Friday 9am to 5pm. We offer free shipping on orders over $50."},
                headers=headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "text"
        assert data["title"] == "Company FAQ"

    @pytest.mark.anyio
    async def test_add_empty_text_returns_422(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        resp = await client.post(
            f"{AGENTS_BASE}/{agent_id}/knowledge/text",
            json={"title": "Empty", "content": "   "},
            headers=headers,
        )
        assert resp.status_code == 422


class TestUploadDocument:
    @pytest.mark.anyio
    async def test_upload_txt_file(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        file_content = b"Our return policy allows returns within 30 days of purchase. Contact support@example.com for help."
        embed_mock, upsert_mock, _ = _mock_embed_and_upsert()
        with embed_mock, upsert_mock:
            resp = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/upload",
                files={"file": ("policy.txt", io.BytesIO(file_content), "text/plain")},
                headers=headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "file"
        assert data["file_name"] == "policy.txt"
        assert data["chunk_count"] >= 1


class TestListKnowledge:
    @pytest.mark.anyio
    async def test_list_empty(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        resp = await client.get(f"{AGENTS_BASE}/{agent_id}/knowledge", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["data"] == []

    @pytest.mark.anyio
    async def test_list_shows_added_sources(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        embed_mock, upsert_mock, _ = _mock_embed_and_upsert()
        with embed_mock, upsert_mock:
            await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "FAQ", "content": "We are open Monday to Friday 9am-5pm."},
                headers=headers,
            )

        resp = await client.get(f"{AGENTS_BASE}/{agent_id}/knowledge", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestDeleteKnowledge:
    @pytest.mark.anyio
    async def test_delete_source(self, client):
        headers = await _register_and_get_headers(client)
        agent_id = await _create_agent(client, headers)

        embed_mock, upsert_mock, del_mock = _mock_embed_and_upsert()
        with embed_mock, upsert_mock, del_mock:
            add = await client.post(
                f"{AGENTS_BASE}/{agent_id}/knowledge/text",
                json={"title": "FAQ", "content": "We are open Monday to Friday 9am-5pm."},
                headers=headers,
            )
            source_id = add.json()["id"]

            resp = await client.delete(
                f"{AGENTS_BASE}/{agent_id}/knowledge/{source_id}",
                headers=headers,
            )

        assert resp.status_code == 204

        list_resp = await client.get(f"{AGENTS_BASE}/{agent_id}/knowledge", headers=headers)
        assert list_resp.json()["total"] == 0
