# Widget (Public Chat)

## Overview

The embeddable chat widget allows agents to be deployed on any website. It provides public endpoints (no auth required) with IP-based rate limiting and session management. The widget is a standalone JavaScript snippet users embed on their sites.

---

## Public Endpoints

| Method | Route | Purpose | Rate Limit |
|--------|-------|---------|-----------|
| GET | `/api/v1/widget/{agent_id}/status` | Agent config for widget UI | 30/min |
| POST | `/api/v1/widget/{agent_id}/chat` | Send message | 10/min |
| GET | `/api/v1/widget/{agent_id}/session` | Restore session | 30/min |

### GET `/widget/{agent_id}/status`
Returns only public agent info:
```json
{
  "name": "Support Bot",
  "welcome_message": "Hello! How can I help?",
  "primary_color": "#6366f1",
  "avatar_url": "https://...",
  "is_live": true
}
```

### POST `/widget/{agent_id}/chat`
```json
// Request
{ "message": "What are your pricing plans?" }

// Response
{
  "message": "Here are our plans...",
  "session_id": "uuid"
}
```

### GET `/widget/{agent_id}/session`
Restores session by client IP → returns recent messages.

---

## Session Management

- Widget sessions use client IP as `session_identifier`
- First message creates a new session
- Session restored on page reload (same IP)
- Sessions expire after 24 hours of inactivity

---

## CORS Configuration

```python
# Allow embedding from any domain
CORSMiddleware(
    allow_origins=["*"],         # Widget can be on any site
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-RateLimit-Remaining"],
)
```

Widget routes have separate CORS rules from the main API.

---

## Rate Limiting

```python
# slowapi rate limiting
@limiter.limit("10/minute")
async def widget_chat(request: Request, agent_id: UUID):
    ...
```

Rate limit headers in response:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1719900000
```

---

## Widget Embed Code

Users get this snippet from the Agent Builder:

```html
<script
  src="https://botlixio.com/widget.js"
  data-agent-id="agent-uuid-here"
  data-position="bottom-right"
></script>
```

The widget.js script:
1. Creates an iframe overlay with the chat UI
2. Calls the widget API endpoints
3. Themed using the agent's `primary_color`
4. Responsive: works on mobile and desktop

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Agent is PAUSED | Return fallback message |
| Agent is DRAFT/deleted | 404 |
| Rate limit exceeded | 429 with retry-after header |
| Empty message | 400 "Message required" |
| Agent owner's plan expired | Use free plan limits |

---

## Business Rules

1. **No auth required**: Widget endpoints are fully public
2. **Rate limiting**: Strictly enforced per IP to prevent abuse
3. **Plan limits still apply**: Widget messages count against agent owner's plan
4. **No history access**: Widget users can only see their own session
5. **Agent must be LIVE**: Only LIVE agents respond via widget

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/widget/{agent_id}/status` | Agent config |
| POST | `/api/v1/widget/{agent_id}/chat` | Send message |
| GET | `/api/v1/widget/{agent_id}/session` | Restore session |
