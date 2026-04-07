"""Integration tests for Widget chat API (public, no auth)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

AGENTS_BASE = "/api/v1/agents"
WIDGET_BASE = "/api/v1/widget"


async def _create_live_agent(client):
    """Register user, create agent, deploy it, return (headers, agent_id)."""
    await client.post("/api/v1/auth/register", json={
        "email": "chatowner@example.com", "password": "password123", "full_name": "Chat Owner"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "chatowner@example.com", "password": "password123"
    })
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    create = await client.post(AGENTS_BASE, json={
        "name": "Support Bot",
        "welcome_message": "Hello! How can I help?",
        "system_prompt": "You are a helpful support agent.",
    }, headers=headers)
    agent_id = create.json()["id"]
    await client.post(f"{AGENTS_BASE}/{agent_id}/deploy", headers=headers)
    return headers, agent_id


class TestWidgetStatus:
    @pytest.mark.anyio
    async def test_status_of_live_agent(self, client):
        _, agent_id = await _create_live_agent(client)
        resp = await client.get(f"{WIDGET_BASE}/{agent_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_live"] is True
        assert data["name"] == "Support Bot"
        assert data["welcome_message"] == "Hello! How can I help?"

    @pytest.mark.anyio
    async def test_status_of_nonexistent_agent(self, client):
        resp = await client.get(f"{WIDGET_BASE}/{uuid.uuid4()}/status")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_status_of_draft_agent_shows_not_live(self, client):
        await client.post("/api/v1/auth/register", json={
            "email": "draftowner@example.com", "password": "password123", "full_name": "Draft Owner"
        })
        login = await client.post("/api/v1/auth/login", json={
            "email": "draftowner@example.com", "password": "password123"
        })
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        create = await client.post(AGENTS_BASE, json={"name": "Draft Bot"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.get(f"{WIDGET_BASE}/{agent_id}/status")
        assert resp.status_code == 200
        assert resp.json()["is_live"] is False


class TestWidgetChat:
    @pytest.mark.anyio
    async def test_chat_with_live_agent(self, client):
        _, agent_id = await _create_live_agent(client)

        with patch("app.services.chat_engine.retrieve", new_callable=AsyncMock, return_value=[]):
            with patch("app.services.chat_engine.chat_completion", new_callable=AsyncMock,
                       return_value="Sure! Our hours are 9am-5pm Monday to Friday."):
                resp = await client.post(f"{WIDGET_BASE}/{agent_id}/chat", json={
                    "message": "What are your opening hours?"
                })

        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"] == "Sure! Our hours are 9am-5pm Monday to Friday."
        assert "session_id" in data

    @pytest.mark.anyio
    async def test_chat_with_draft_agent_returns_fallback(self, client):
        await client.post("/api/v1/auth/register", json={
            "email": "draftchat@example.com", "password": "password123", "full_name": "Draft"
        })
        login = await client.post("/api/v1/auth/login", json={
            "email": "draftchat@example.com", "password": "password123"
        })
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        create = await client.post(AGENTS_BASE, json={
            "name": "Draft Bot",
            "fallback_message": "Not available right now.",
        }, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.post(f"{WIDGET_BASE}/{agent_id}/chat", json={"message": "Hello"})
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Not available right now."

    @pytest.mark.anyio
    async def test_chat_session_persists_across_messages(self, client):
        _, agent_id = await _create_live_agent(client)

        with patch("app.services.chat_engine.retrieve", new_callable=AsyncMock, return_value=[]):
            with patch("app.services.chat_engine.chat_completion", new_callable=AsyncMock,
                       return_value="First reply"):
                r1 = await client.post(f"{WIDGET_BASE}/{agent_id}/chat", json={
                    "message": "Hello",
                    "session_id": "test-session-123",
                })
            with patch("app.services.chat_engine.chat_completion", new_callable=AsyncMock,
                       return_value="Second reply"):
                r2 = await client.post(f"{WIDGET_BASE}/{agent_id}/chat", json={
                    "message": "Follow up",
                    "session_id": "test-session-123",
                })

        # Both should return a session_id (UUID of the DB session)
        assert r1.status_code == 200
        assert r2.status_code == 200

    @pytest.mark.anyio
    async def test_chat_nonexistent_agent_returns_404(self, client):
        resp = await client.post(f"{WIDGET_BASE}/{uuid.uuid4()}/chat", json={
            "message": "Hello"
        })
        assert resp.status_code == 404
