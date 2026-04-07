"""Integration tests for Agent CRUD API endpoints."""

import pytest

BASE = "/api/v1/agents"


async def _register_and_login(client, email="agentuser@example.com", password="password123"):
    await client.post("/api/v1/auth/register", json={
        "email": email, "password": password, "full_name": "Agent User"
    })
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def _auth_headers(client, email="agentuser@example.com", password="password123"):
    token = await _register_and_login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


class TestCreateAgent:
    @pytest.mark.anyio
    async def test_create_returns_201(self, client):
        headers = await _auth_headers(client)
        resp = await client.post(BASE, json={"name": "Support Bot"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Support Bot"
        assert data["status"] == "draft"
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_with_all_fields(self, client):
        headers = await _auth_headers(client)
        payload = {
            "name": "Full Bot",
            "description": "A fully configured bot",
            "system_prompt": "You are a pizza shop assistant.",
            "welcome_message": "Welcome! How can I help?",
            "fallback_message": "I didn't get that.",
            "primary_color": "#2513EC",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 512,
        }
        resp = await client.post(BASE, json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "A fully configured bot"
        assert data["primary_color"] == "#2513EC"

    @pytest.mark.anyio
    async def test_create_requires_auth(self, client):
        resp = await client.post(BASE, json={"name": "Bot"})
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_create_enforces_free_plan_limit(self, client):
        headers = await _auth_headers(client)
        for i in range(3):
            r = await client.post(BASE, json={"name": f"Bot {i}"}, headers=headers)
            assert r.status_code == 201
        resp = await client.post(BASE, json={"name": "Bot 4"}, headers=headers)
        assert resp.status_code == 403
        assert "3" in resp.json()["detail"]

    @pytest.mark.anyio
    async def test_create_invalid_color_returns_422(self, client):
        headers = await _auth_headers(client)
        resp = await client.post(BASE, json={"name": "Bot", "primary_color": "notacolor"}, headers=headers)
        assert resp.status_code == 422


class TestListAgents:
    @pytest.mark.anyio
    async def test_list_returns_empty_initially(self, client):
        headers = await _auth_headers(client)
        resp = await client.get(BASE, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"] == []
        assert resp.json()["total"] == 0

    @pytest.mark.anyio
    async def test_list_returns_only_own_agents(self, client):
        h1 = await _auth_headers(client, "user1@example.com")
        h2 = await _auth_headers(client, "user2@example.com")
        await client.post(BASE, json={"name": "User1 Bot"}, headers=h1)
        await client.post(BASE, json={"name": "User2 Bot"}, headers=h2)

        resp1 = await client.get(BASE, headers=h1)
        assert resp1.json()["total"] == 1
        assert resp1.json()["data"][0]["name"] == "User1 Bot"

        resp2 = await client.get(BASE, headers=h2)
        assert resp2.json()["total"] == 1


class TestGetAgent:
    @pytest.mark.anyio
    async def test_get_own_agent(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "My Bot"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.get(f"{BASE}/{agent_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == agent_id

    @pytest.mark.anyio
    async def test_get_other_user_agent_returns_403(self, client):
        h1 = await _auth_headers(client, "owner@example.com")
        h2 = await _auth_headers(client, "thief@example.com")
        create = await client.post(BASE, json={"name": "Bot"}, headers=h1)
        agent_id = create.json()["id"]

        resp = await client.get(f"{BASE}/{agent_id}", headers=h2)
        assert resp.status_code == 403

    @pytest.mark.anyio
    async def test_get_nonexistent_returns_404(self, client):
        headers = await _auth_headers(client)
        resp = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000", headers=headers)
        assert resp.status_code == 404


class TestUpdateAgent:
    @pytest.mark.anyio
    async def test_update_name(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Old Name"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.patch(f"{BASE}/{agent_id}", json={"name": "New Name"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    @pytest.mark.anyio
    async def test_update_other_user_returns_403(self, client):
        h1 = await _auth_headers(client, "owner@example.com")
        h2 = await _auth_headers(client, "thief@example.com")
        create = await client.post(BASE, json={"name": "Bot"}, headers=h1)
        agent_id = create.json()["id"]

        resp = await client.patch(f"{BASE}/{agent_id}", json={"name": "Hacked"}, headers=h2)
        assert resp.status_code == 403


class TestDeleteAgent:
    @pytest.mark.anyio
    async def test_delete_returns_204(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Bye Bot"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.delete(f"{BASE}/{agent_id}", headers=headers)
        assert resp.status_code == 204

        get_resp = await client.get(f"{BASE}/{agent_id}", headers=headers)
        assert get_resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_other_user_returns_403(self, client):
        h1 = await _auth_headers(client, "owner@example.com")
        h2 = await _auth_headers(client, "thief@example.com")
        create = await client.post(BASE, json={"name": "Bot"}, headers=h1)
        agent_id = create.json()["id"]

        resp = await client.delete(f"{BASE}/{agent_id}", headers=h2)
        assert resp.status_code == 403


class TestDeployPause:
    @pytest.mark.anyio
    async def test_deploy_changes_status_to_live(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Bot"}, headers=headers)
        agent_id = create.json()["id"]
        assert create.json()["status"] == "draft"

        resp = await client.post(f"{BASE}/{agent_id}/deploy", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "live"

    @pytest.mark.anyio
    async def test_deploy_already_live_returns_400(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Bot"}, headers=headers)
        agent_id = create.json()["id"]
        await client.post(f"{BASE}/{agent_id}/deploy", headers=headers)

        resp = await client.post(f"{BASE}/{agent_id}/deploy", headers=headers)
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_pause_live_agent(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Bot"}, headers=headers)
        agent_id = create.json()["id"]
        await client.post(f"{BASE}/{agent_id}/deploy", headers=headers)

        resp = await client.post(f"{BASE}/{agent_id}/pause", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

    @pytest.mark.anyio
    async def test_pause_draft_returns_400(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Bot"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.post(f"{BASE}/{agent_id}/pause", headers=headers)
        assert resp.status_code == 400


class TestEmbedCode:
    @pytest.mark.anyio
    async def test_embed_code_returns_snippet(self, client):
        headers = await _auth_headers(client)
        create = await client.post(BASE, json={"name": "Support Bot"}, headers=headers)
        agent_id = create.json()["id"]

        resp = await client.get(f"{BASE}/{agent_id}/embed-code", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert agent_id in data["snippet"]
        assert "widget.js" in data["snippet"]
        assert "BotlixioAgentId" in data["snippet"]
