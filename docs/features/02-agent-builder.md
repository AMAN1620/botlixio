# Agent Builder

## Overview

The Agent Builder is the core feature of Botlixio. Users create AI agents by selecting an LLM provider/model, writing a system prompt, choosing tools, and configuring deployment channels. Each agent has its own knowledge base, chat history, and lead collection.

---

## Data Model

See [database-schema.md](../database-schema.md) → `Agent` model.

Key fields:
- `provider` + `model`: LLM configuration (restricted by user's plan)
- `system_prompt`: The agent's personality and instructions
- `tools`: JSONB list of enabled tool slugs
- `channels`: JSONB list of channel configs
- `status`: `DRAFT` → `LIVE` → `PAUSED`
- `total_messages`, `total_sessions`: Lifetime counters

---

## Pages

### `/agents` — Agent List
- Grid of agent cards: Name, description, model, status, messages count
- Status toggle (LIVE/PAUSED) directly on card
- "Create Agent" button → `/agents/new`
- Filter by status
- Empty state: "Create your first AI agent"

### `/agents/new` — Create Agent (Multi-Step Wizard)

**Step 1: Basics**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Name | Text | Yes | e.g., "Support Bot" |
| Description | Textarea | No | Internal description |

**Step 2: LLM Configuration**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Provider | Select | Yes | OpenAI / Anthropic / Google (filtered by plan) |
| Model | Select | Yes | Models available for selected provider + plan |
| Temperature | Slider | Yes | 0.0 – 2.0, default 0.7 |
| Max Tokens | Number | Yes | 256 – 4096, default 1024 |

**Step 3: System Prompt**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| System Prompt | Code editor | Yes | Markdown-enabled textarea |
| Welcome Message | Text | No | First message shown to users |
| Fallback Message | Text | No | Shown when agent is paused |

**Step 4: Tools**
- Checklist of available tools (filtered by plan):
  - Web Search — search the internet for real-time info
  - Weather — get current weather for a location
  - Lead Catcher — automatically capture contact details

**Step 5: Appearance**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Primary Color | Color picker | No | Widget theme color |
| Avatar | Image upload | No | Agent avatar for widget |

**Step 6: Review & Create**
- Summary of all settings
- "Create as Draft" button → creates agent in DRAFT status

### `/agents/[id]` — Agent Detail

Tabbed layout:

| Tab | Content |
|-----|---------|
| Settings | All agent config (editable) |
| Knowledge | Knowledge base management (linked to [Knowledge Base](05-knowledge-base.md)) |
| Test Chat | Live chat interface for testing |
| Leads | Captured leads table (linked to lead capture) |
| Analytics | Message count, session count, response time |

### `/agents/[id]/edit` — Same as Settings tab

---

## Agent Status Lifecycle

```
DRAFT → LIVE (deploy)
LIVE → PAUSED (pause)
PAUSED → LIVE (resume)
```

- **DRAFT**: Agent is being configured. Not accessible via public endpoints.
- **LIVE**: Agent accepts and responds to messages from all configured channels.
- **PAUSED**: Agent returns fallback message only.

---

## Plan Limit Check on Create

```
Before creating:
  1. Get user's subscription
  2. Count user's existing agents (exclude deleted)
  3. If count >= plan.max_agents → PlanLimitExceeded
  4. If agent.model not in plan.allowed_models → ModelNotAllowed
```

---

## Model Access by Plan

| Plan | Models |
|------|--------|
| Free | gpt-4o-mini |
| Starter | gpt-4o-mini, gpt-4o, claude-3-haiku |
| Growth | + claude-3.5-sonnet, gemini-pro |
| Business | All models |

BYOK users (Growth, Business plans) can use any LiteLLM-supported model.

---

## Business Rules

1. **Agent soft-delete**: Deleting an agent sets a deleted flag; chat history and leads are preserved
2. **Model validation**: Agent model must be in user's plan allowed_models (or BYOK)
3. **Tool validation**: Agent tools must be active in platform tool_configs AND user's plan allowed_tools
4. **Unique names per user**: Agent names must be unique per user
5. **Ownership**: Only the agent owner can view, edit, or delete their agents

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/agents` | List user's agents |
| POST | `/api/v1/agents` | Create agent |
| GET | `/api/v1/agents/{id}` | Get agent detail |
| PUT | `/api/v1/agents/{id}` | Update agent |
| DELETE | `/api/v1/agents/{id}` | Soft-delete agent |
| POST | `/api/v1/agents/{id}/deploy` | Set status to LIVE |
| POST | `/api/v1/agents/{id}/pause` | Set status to PAUSED |
| GET | `/api/v1/agents/{id}/stats` | Agent analytics |
