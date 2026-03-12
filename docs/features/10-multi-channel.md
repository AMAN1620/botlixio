# Multi-Channel Deployment

## Overview

Agents can be deployed across multiple channels beyond the web widget. Each channel receives incoming messages via webhooks, normalizes them, processes through the chat engine, and sends responses back through the channel-specific API.

---

## Supported Channels

| Channel | Incoming | Outgoing | Auth Method |
|---------|----------|----------|-------------|
| Widget | HTTP POST | HTTP Response | None (public) |
| WhatsApp | Baileys webhook | Baileys send | QR Code pairing |
| Discord | Bot webhook | Bot reply | Bot Token |
| Slack | Events API | Web API | Bot Token + App |

---

## Architecture

```
Channel-Specific Webhook → Normalize → Chat Engine → Response → Channel-Specific Send
                              ↓
                        Unified format:
                        {channel, sender_id, message, agent_id, metadata}
```

---

## WhatsApp (via Baileys Bridge)

### Setup
The WhatsApp bridge is a separate Node.js service using the Baileys library (unofficial WhatsApp Web API).

```
whatsapp-bridge/
├── src/
│   ├── index.js          # Express + Baileys client
│   └── qr-server.js      # QR code streaming for authentication
├── package.json
└── Dockerfile
```

### Authentication
1. Admin opens bridge auth page
2. QR code displayed (SSE stream)
3. User scans with WhatsApp → session authenticated
4. Session persisted to disk for reconnection

### Message Flow
```
1. WhatsApp message received → Baileys triggers event
2. Bridge parses message: { from: phone, body: text }
3. Bridge POST to backend: /api/v1/webhooks/whatsapp
   {
     "sender_id": "919876543210",
     "message": "What are your office hours?",
     "agent_id": "mapped-agent-uuid"
   }
4. Backend processes through chat engine
5. Backend returns: { "reply": "Our hours are 9-5..." }
6. Bridge sends reply via Baileys to the phone number
```

### Agent Mapping
- Admin maps phone number → agent via channel config
- Each WhatsApp number routes to one agent

---

## Discord

### Setup
1. Create Discord Bot in Discord Developer Portal
2. Get Bot Token
3. Configure webhook URL in bot settings: `https://api.botlixio.com/api/v1/webhooks/discord`
4. Add bot to server with message read/write permissions

### Message Flow
```
1. User sends message in channel/DM where bot is present
2. Discord sends webhook to /api/v1/webhooks/discord
   {
     "type": 1,   // MESSAGE_CREATE
     "data": {
       "content": "What are your pricing plans?",
       "author": { "id": "discord-user-id", "username": "john" },
       "channel_id": "channel-id"
     }
   }
3. Backend normalizes → processes through chat engine
4. Backend responds via Discord API:
   POST https://discord.com/api/v10/channels/{channel_id}/messages
   { "content": "Here are our plans..." }
```

### Agent Mapping
- Channel ID → Agent mapping via channel config
- One Discord channel = one agent

---

## Slack

### Setup
1. Create Slack App in api.slack.com
2. Enable Events API → subscribe to `message.channels`, `message.im`
3. Set Request URL: `https://api.botlixio.com/api/v1/webhooks/slack`
4. Get Bot Token (xoxb-...) with `chat:write` scope

### Message Flow
```
1. User messages in channel/DM with bot
2. Slack sends event:
   {
     "type": "event_callback",
     "event": {
       "type": "message",
       "text": "How do I get started?",
       "user": "U12345",
       "channel": "C67890"
     }
   }
3. Backend normalizes → chat engine → response
4. Backend replies via Slack API:
   POST https://slack.com/api/chat.postMessage
   { "channel": "C67890", "text": "Welcome! Here's how..." }
```

### Agent Mapping
- Slack Channel → Agent mapping
- Or: DM with bot → default agent for that workspace

---

## Message Normalization

```python
# app/api/v1/webhooks.py

def normalize_whatsapp(payload: dict) -> dict:
    return {
        "channel": "whatsapp",
        "sender_id": payload["sender_id"],
        "message": payload["message"],
        "agent_id": lookup_agent("whatsapp", payload["sender_id"]),
        "metadata": {"phone": payload["sender_id"]}
    }

def normalize_discord(payload: dict) -> dict:
    return {
        "channel": "discord",
        "sender_id": payload["data"]["author"]["id"],
        "message": payload["data"]["content"],
        "agent_id": lookup_agent("discord", payload["data"]["channel_id"]),
        "metadata": {"channel_id": payload["data"]["channel_id"]}
    }

def normalize_slack(payload: dict) -> dict:
    return {
        "channel": "slack",
        "sender_id": payload["event"]["user"],
        "message": payload["event"]["text"],
        "agent_id": lookup_agent("slack", payload["event"]["channel"]),
        "metadata": {"channel_id": payload["event"]["channel"]}
    }
```

---

## Channel Configuration

Admin manages channel → agent mappings:

```python
# Example channel config stored on Agent.channels JSONB
[
    {
        "type": "widget",
        "enabled": true
    },
    {
        "type": "whatsapp",
        "enabled": true,
        "phone_number": "919876543210"
    },
    {
        "type": "discord",
        "enabled": true,
        "channel_id": "1234567890"
    },
    {
        "type": "slack",
        "enabled": true,
        "channel_id": "C67890"
    }
]
```

---

## Channel Access by Plan

| Channel | Free | Starter | Growth | Business |
|---------|------|---------|--------|----------|
| Widget | ✅ | ✅ | ✅ | ✅ |
| WhatsApp | ❌ | ✅ | ✅ | ✅ |
| Discord | ❌ | ❌ | ✅ | ✅ |
| Slack | ❌ | ❌ | ✅ | ✅ |

---

## Business Rules

1. **Unified processing**: All channels use the same chat engine — consistent responses
2. **Session per channel**: Same agent can have separate sessions per channel
3. **Plan limits**: Messages from all channels count against the same monthly limit
4. **Agent must be LIVE**: Only LIVE agents respond on any channel
5. **Webhook validation**: Each channel has its own signature verification
6. **Bot mention filtering**: Discord/Slack only process messages mentioning the bot

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/v1/webhooks/whatsapp` | WhatsApp incoming |
| POST | `/api/v1/webhooks/discord` | Discord incoming |
| POST | `/api/v1/webhooks/slack` | Slack incoming |
