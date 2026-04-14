"""Integration tests for Widget chat API (public, no auth)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.integration.conftest import make_verified_token

AGENTS_BASE = "/api/v1/agents"
WIDGET_BASE = "/api/v1/widget"


async def _create_live_agent(client, db_engine):
    """Register a verified user, create agent, deploy it, return (headers, agent_id)."""
    token = await make_verified_token(
        client, db_engine, "chatowner@example.com", "password123", "Chat Owner"
    )
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        AGENTS_BASE,
        json={"name": "Support Bot", "welcome_message": "Hello! How can I help?"},
        headers=headers,
    )
    agent_id = create.json()["id"]
    await client.post(f"{AGENTS_BASE}/{agent_id}/deploy", headers=headers)
    return headers, agent_id


class TestWidgetStatus:
    @pytest.mark.anyio
    async def test_status_of_live_agent(self, client, db_engine):
        _, agent_id = await _create_live_agent(client, db_engine)
        resp = await client.get(f"{WIDGET_BASE}/{agent_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_live"] is True
        assert data["name"] == "Support Bot"
        assert data["welcome_message"] == "Hello! How can I help?"

    @pytest.mark.anyio
    async def test_status_of_nonexistent_agent(self, client, db_engine):
        resp = await client.get(f"{WIDGET_BASE}/{uuid.uuid4()}/status")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_status_of_draft_agent_shows_not_live(self, client, db_engine):
        token = await make_verified_token(
            client, db_engine, "draftowner@example.com", "password123", "Draft Owner"
        )
        headers = {"Authorization": f"Bearer {token}"}
        create = await client.post(AGENTS_BASE, json={"name": "Draft Bot"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.get(f"{WIDGET_BASE}/{agent_id}/status")
        assert resp.status_code == 200
        assert resp.json()["is_live"] is False


class TestWidgetChat:
    @pytest.mark.anyio
    async def test_chat_with_live_agent(self, client, db_engine):
        _, agent_id = await _create_live_agent(client, db_engine)

        fake_chunks = [{"source_title": "FAQ", "text": "We are open 9am-5pm Monday to Friday."}]
        with patch("app.services.chat_engine.retrieve", new_callable=AsyncMock, return_value=fake_chunks):
            with patch(
                "app.services.chat_engine.chat_completion",
                new_callable=AsyncMock,
                return_value="Sure! Our hours are 9am-5pm Monday to Friday.",
            ):
                resp = await client.post(
                    f"{WIDGET_BASE}/{agent_id}/chat",
                    json={"message": "What are your opening hours?"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"] == "Sure! Our hours are 9am-5pm Monday to Friday."
        assert "session_id" in data

    @pytest.mark.anyio
    async def test_chat_with_draft_agent_returns_fallback(self, client, db_engine):
        token = await make_verified_token(
            client, db_engine, "draftchat@example.com", "password123", "Draft"
        )
        headers = {"Authorization": f"Bearer {token}"}
        create = await client.post(
            AGENTS_BASE,
            json={"name": "Draft Bot", "fallback_message": "Not available right now."},
            headers=headers,
        )
        agent_id = create.json()["id"]

        resp = await client.post(
            f"{WIDGET_BASE}/{agent_id}/chat", json={"message": "Hello"}
        )
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Not available right now."

    @pytest.mark.anyio
    async def test_chat_session_persists_across_messages(self, client, db_engine):
        _, agent_id = await _create_live_agent(client, db_engine)

        fake_chunks = [{"source_title": "FAQ", "text": "Some knowledge content."}]
        with patch("app.services.chat_engine.retrieve", new_callable=AsyncMock, return_value=fake_chunks):
            with patch(
                "app.services.chat_engine.chat_completion",
                new_callable=AsyncMock,
                return_value="First reply",
            ):
                r1 = await client.post(
                    f"{WIDGET_BASE}/{agent_id}/chat",
                    json={"message": "Hello", "session_id": "test-session-123"},
                )
            with patch(
                "app.services.chat_engine.chat_completion",
                new_callable=AsyncMock,
                return_value="Second reply",
            ):
                r2 = await client.post(
                    f"{WIDGET_BASE}/{agent_id}/chat",
                    json={"message": "Follow up", "session_id": "test-session-123"},
                )

        assert r1.status_code == 200
        assert r2.status_code == 200

    @pytest.mark.anyio
    async def test_chat_nonexistent_agent_returns_404(self, client, db_engine):
        resp = await client.post(
            f"{WIDGET_BASE}/{uuid.uuid4()}/chat", json={"message": "Hello"}
        )
        assert resp.status_code == 404
