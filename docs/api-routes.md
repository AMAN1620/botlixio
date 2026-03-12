# API Routes

All routes are under `/api/v1/` and use FastAPI. All routes (except public widget and webhooks) require JWT Bearer authentication.

---

## Authentication

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | Public |
| POST | `/api/v1/auth/login` | Login, returns tokens | Public |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh token |
| POST | `/api/v1/auth/verify-email` | Verify email with token | Public |
| POST | `/api/v1/auth/forgot-password` | Request password reset email | Public |
| POST | `/api/v1/auth/reset-password` | Reset password with token | Public |
| GET | `/api/v1/auth/me` | Get current user profile | User |
| GET | `/api/v1/auth/google` | Google OAuth redirect | Public |
| GET | `/api/v1/auth/google/callback` | Google OAuth callback | Public |

---

## Agents

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/agents` | List user's agents | User |
| POST | `/api/v1/agents` | Create agent (checks plan limit) | User |
| GET | `/api/v1/agents/{id}` | Get agent detail | Owner |
| PUT | `/api/v1/agents/{id}` | Update agent | Owner |
| DELETE | `/api/v1/agents/{id}` | Soft-delete agent | Owner |
| POST | `/api/v1/agents/{id}/deploy` | Set status to LIVE | Owner |
| POST | `/api/v1/agents/{id}/pause` | Set status to PAUSED | Owner |
| GET | `/api/v1/agents/{id}/stats` | Agent analytics | Owner |

---

## Chat (Authenticated)

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/api/v1/chat/{agent_id}` | Send message, get reply | Owner |
| GET | `/api/v1/chat/{agent_id}/sessions` | List chat sessions | Owner |
| GET | `/api/v1/chat/{agent_id}/sessions/{session_id}` | Get session messages | Owner |
| DELETE | `/api/v1/chat/{agent_id}/sessions/{session_id}` | Clear session | Owner |

---

## Widget (Public Chat)

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/widget/{agent_id}/status` | Agent name, avatar, welcome msg | Public |
| POST | `/api/v1/widget/{agent_id}/chat` | Send message (IP-based session) | Public |
| GET | `/api/v1/widget/{agent_id}/session` | Restore session by IP | Public |

Rate limited: 10 msg/min per IP.

---

## Knowledge Base

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/agents/{agent_id}/knowledge` | List knowledge items | Owner |
| POST | `/api/v1/agents/{agent_id}/knowledge/file` | Upload file (PDF/TXT/CSV/DOCX) | Owner |
| POST | `/api/v1/agents/{agent_id}/knowledge/url` | Scrape URL | Owner |
| POST | `/api/v1/agents/{agent_id}/knowledge/text` | Add raw text | Owner |
| DELETE | `/api/v1/agents/{agent_id}/knowledge/{id}` | Delete knowledge item | Owner |

---

## Leads

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/agents/{agent_id}/leads` | List leads for agent | Owner |
| GET | `/api/v1/agents/{agent_id}/leads/export` | Export leads as CSV | Owner |
| DELETE | `/api/v1/agents/{agent_id}/leads/{id}` | Delete lead | Owner |

---

## Billing

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/billing/plans` | List available plans | Public |
| GET | `/api/v1/billing/subscription` | Get user's subscription | User |
| POST | `/api/v1/billing/checkout` | Create Stripe checkout session | User |
| POST | `/api/v1/billing/portal` | Create Stripe billing portal | User |
| POST | `/api/v1/billing/cancel` | Cancel subscription | User |
| POST | `/api/v1/billing/webhook` | Stripe webhook handler | Stripe |

---

## Workflows

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/workflows` | List workflows | User |
| POST | `/api/v1/workflows` | Create workflow | User |
| GET | `/api/v1/workflows/{id}` | Get workflow detail | Owner |
| PUT | `/api/v1/workflows/{id}` | Update workflow | Owner |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow | Owner |
| POST | `/api/v1/workflows/{id}/activate` | Activate workflow | Owner |
| POST | `/api/v1/workflows/{id}/pause` | Pause workflow | Owner |
| GET | `/api/v1/workflows/{id}/executions` | List execution history | Owner |

---

## Integrations

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/integrations` | List user's connected integrations | User |
| POST | `/api/v1/integrations/{provider}/connect` | Connect integration | User |
| DELETE | `/api/v1/integrations/{provider}/disconnect` | Disconnect integration | User |
| POST | `/api/v1/integrations/{provider}/test` | Test integration credentials | User |

---

## Profile

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/profile` | Get user profile | User |
| PUT | `/api/v1/profile` | Update profile | User |
| PUT | `/api/v1/profile/password` | Change password | User |
| PUT | `/api/v1/profile/api-key` | Set own LLM API key (BYOK) | User |

---

## Admin

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| GET | `/api/v1/admin/users` | List all users | Admin |
| GET | `/api/v1/admin/users/{id}` | Get user detail | Admin |
| PUT | `/api/v1/admin/users/{id}` | Update user (role, active) | Admin |
| POST | `/api/v1/admin/users/{id}/block` | Block user | Admin |
| GET | `/api/v1/admin/analytics` | Platform analytics | Admin |
| GET | `/api/v1/admin/api-keys` | List platform API keys (masked) | Admin |
| POST | `/api/v1/admin/api-keys` | Add platform API key | Admin |
| DELETE | `/api/v1/admin/api-keys/{id}` | Delete platform API key | Admin |
| GET | `/api/v1/admin/pricing` | Get pricing config | Admin |
| PUT | `/api/v1/admin/pricing` | Update pricing config | Admin |
| GET | `/api/v1/admin/tools` | List tool configs | Admin |
| POST | `/api/v1/admin/tools` | Create tool config | Admin |
| PUT | `/api/v1/admin/tools/{id}` | Update tool config | Admin |
| DELETE | `/api/v1/admin/tools/{id}` | Delete tool config | Admin |
| GET | `/api/v1/admin/channels` | List channel configs | Admin |
| POST | `/api/v1/admin/channels` | Create channel config | Admin |
| PUT | `/api/v1/admin/channels/{id}` | Update channel config | Admin |
| DELETE | `/api/v1/admin/channels/{id}` | Delete channel config | Admin |

---

## Webhooks (Incoming)

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/api/v1/webhooks/whatsapp` | WhatsApp incoming message | WA Bridge |
| POST | `/api/v1/webhooks/discord` | Discord incoming message | Discord |
| POST | `/api/v1/webhooks/slack` | Slack incoming message | Slack |

---

## Standard Response Formats

### Success (list)
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Success (single)
```json
{
  "data": { ... }
}
```

### Error
```json
{
  "detail": "Error message"
}
```
or (validation error)
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "value_error" }
  ]
}
```

### HTTP Status Codes
| Status | Usage |
|--------|-------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted (no content) |
| 400 | Validation error |
| 401 | Unauthenticated |
| 403 | Forbidden (wrong role / not owner) |
| 404 | Not found |
| 409 | Conflict (duplicate email) |
| 429 | Rate limited |
| 500 | Internal server error |
