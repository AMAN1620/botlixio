# Build Plan: RAG Pipeline + Agent Wizard + WhatsApp

> Covers the decisions from the brainstorm session.
> Prerequisites: Phases 0–3 done. Phase 4–6 services exist in backend but need the upgrades below.

---

## What we are building

1. **Upgraded RAG pipeline** — 2-phase URL crawl (link discovery → selective scrape), async background indexing, per-source status tracking
2. **Agent creation wizard** — 4-step wizard with DRAFT auto-save, "still indexing" live banner
3. **WhatsApp via Baileys** — Node.js microservice, QR pairing flow, message bridge to FastAPI
4. **Website widget** — vanilla JS embed, floating chat button

---

## Architecture decisions locked in

| Decision | Choice | Reason |
|---|---|---|
| Crawling | Crawl4AI (self-hosted) |
| Max pages per crawl | User-set (1–20, default 10) | User controls scope; review + remove/add after crawl |
| Chunking | 512 tokens, 50 overlap, paragraph-aware | Already implemented, correct |
| Vector storage | Qdrant — one shared collection, filter by `agent_id` | Scales vs per-agent collections |
| Background jobs | ARQ (async Redis queue) | Fits async FastAPI stack, Redis already present |
| WhatsApp | Baileys (Node.js microservice) | Free, no Meta approval needed for v1 |
| Agent wizard | 4-step with DRAFT auto-save | Go Live allowed with partially-indexed sources |

---

## Phase A: Data model upgrades (prerequisite for everything)

**Goal**: `KnowledgeItem` needs per-source status. Without this, no async indexing UX is possible.

### A1 — Migration: add status fields to `AgentKnowledge`

Add to `app/models/knowledge.py`:
```python
class IndexingStatus(str, Enum):
    PENDING    = "pending"     # added, not yet processed
    PROCESSING = "processing"  # ARQ job running
    INDEXED    = "indexed"     # chunks in Qdrant, ready
    FAILED     = "failed"      # error during processing
    STALE      = "stale"       # source changed, needs re-index

# New columns on AgentKnowledge:
indexing_status: Mapped[IndexingStatus] = mapped_column(default=IndexingStatus.PENDING)
content_hash:    Mapped[str | None]     = mapped_column(String(64), nullable=True)
error_message:   Mapped[str | None]     = mapped_column(Text, nullable=True)
indexed_at:      Mapped[datetime | None] = mapped_column(nullable=True)
```

- [ ] Add `IndexingStatus` enum to `app/models/enums.py`
- [ ] Add 4 new columns to `AgentKnowledge` model
- [ ] `alembic revision --autogenerate -m "knowledge_indexing_status"`
- [ ] `alembic upgrade head`
- [ ] Update `KnowledgeResponse` schema to include `indexing_status`, `error_message`, `indexed_at`
- [ ] Update `KnowledgeRepository` — add `update_status(id, status, error=None)` method
- [ ] Test: status transitions (PENDING → PROCESSING → INDEXED, PENDING → FAILED)

**Done when**: `AgentKnowledge` has status fields, repo can update them, schema exposes them.

---

## Phase B: Task queue setup (prerequisite for async indexing)

**Goal**: Background jobs for crawl + chunk + embed pipeline.

### B1 — ARQ setup

```
pip install arq
```

- [ ] `backend/app/core/arq_pool.py` — Redis pool for ARQ (reuse `REDIS_URL` from config)
- [ ] `backend/app/workers/` — worker package
- [ ] `backend/app/workers/knowledge_worker.py` — job functions:
  - `index_url_source(ctx, knowledge_id, url, agent_id)` — crawl → chunk → embed → update status
  - `index_file_source(ctx, knowledge_id, file_path, agent_id)` — parse → chunk → embed → update status
  - `index_text_source(ctx, knowledge_id, text, agent_id)` — chunk → embed → update status
  - `delete_source_vectors(ctx, agent_id, knowledge_id)` — remove from Qdrant
- [ ] `backend/arq_worker.py` (entry point) — `WorkerSettings` with Redis DSN + job list
- [ ] Each job: set status PROCESSING on start, INDEXED on success, FAILED on error (save `error_message`)
- [ ] Test: mock ARQ context, job functions execute pipeline, status updates correctly
- [ ] `docker/docker-compose.yml` — add `arq_worker` service:
  ```yaml
  arq_worker:
    build: ./backend
    command: arq arq_worker.WorkerSettings
    depends_on: [postgres, redis]
    env_file: ./backend/.env
  ```

**Done when**: `docker compose up arq_worker` starts, jobs enqueue and execute in background.

---

## Phase C: Crawler upgrades — 2-phase flow

**Goal**: Phase 1 = link discovery only (fast). Phase 2 = scrape selected links (async job).

### C1 — Crawl endpoint (crawl first, review after)

No upfront link selection. User sets the target and fires — results are reviewed after crawling completes.

`POST /agents/{id}/knowledge/url`

```
Request:  {
  "root_url":    "https://example.com",
  "path_filter": "/docs",      ← optional — only crawl URLs containing this prefix
  "max_pages":   10            ← user-set, 1–20 (default 10)
}
Response: { "knowledge_id": "uuid", "status": "pending" }   # returns immediately
```

- Create `AgentKnowledge` record with `status=PENDING`, store `root_url`, `path_filter`, `max_pages`
- Enqueue ARQ job `index_url_source` immediately — no pre-selection step
- Job runs: crawl from `root_url`, respect `path_filter`, stop at `max_pages` → markdown → chunk → embed → INDEXED
- After INDEXED: store `crawled_pages` (JSONB list of `{ url, title, char_count }`) on the record so user can see exactly what was crawled

```python
# stored on AgentKnowledge after indexing:
crawled_pages = [
  { "url": "https://example.com/docs/intro",    "title": "Introduction",    "char_count": 3200 },
  { "url": "https://example.com/docs/api",      "title": "API Reference",   "char_count": 8100 },
  ...
]
```

- [ ] Add columns to `AgentKnowledge`: `root_url`, `path_filter`, `max_pages: int`, `crawled_pages: JSONB`
- [ ] Migration for new columns
- [ ] `knowledge_service.add_url_source()` — create record, enqueue ARQ job, return immediately
- [ ] ARQ job stores `crawled_pages` list on completion
- [ ] `app/schemas/knowledge.py` — `KnowledgeUrlRequest` with `root_url`, `path_filter` (optional), `max_pages`
- [ ] Test: crawl returns immediately with PENDING, job indexes pages, `crawled_pages` populated on completion
- [ ] Test: `path_filter` restricts crawled URLs to matching prefix
- [ ] Test: `max_pages` cap respected

### C2 — Status polling endpoint

`GET /agents/{id}/knowledge/{knowledge_id}/status`

```json
{
  "id": "uuid",
  "status": "processing",
  "indexed_at": null,
  "error_message": null,
  "chunk_count": 0,
  "crawled_pages": []    ← populated once indexed
}
```

- [ ] `app/api/v1/knowledge.py` — add status endpoint
- [ ] Frontend polls every 3s until `status == "indexed"` or `"failed"`
- [ ] Once indexed, frontend renders `crawled_pages` as a reviewable list (page title + char count)

### C3 — Remove a crawled page from source

`DELETE /agents/{id}/knowledge/{knowledge_id}/pages`

```
Request:  { "url": "https://example.com/docs/some-page" }
Response: 204 No Content
```

- User sees crawled pages after indexing, removes ones they don't want
- Deletes chunks from Qdrant that originated from this specific URL (filter by `source_id + url`)
- Removes the entry from `crawled_pages` JSONB list
- Does NOT re-index — just surgically removes that page's vectors

- [ ] `knowledge_service.remove_crawled_page(knowledge_id, url)` — targeted Qdrant delete + update JSONB
- [ ] `DELETE /agents/{id}/knowledge/{knowledge_id}/pages` endpoint
- [ ] Test: removing a page deletes its vectors, updates `crawled_pages` list

### C4 — Add a missing page manually

`POST /agents/{id}/knowledge/{knowledge_id}/pages`

```
Request:  { "url": "https://example.com/docs/missing-page" }
Response: { "status": "pending" }
```

- User can add a specific URL that the crawl missed
- Enqueues a targeted single-page scrape job
- Appends result to existing `crawled_pages` list on completion
- Does NOT re-index the whole source

- [ ] `knowledge_service.add_page_to_source(knowledge_id, url)` — enqueue single-page job, append to `crawled_pages`
- [ ] `POST /agents/{id}/knowledge/{knowledge_id}/pages` endpoint
- [ ] Test: added page gets scraped and appended, existing pages unaffected

---

## Phase D: Frontend — Agent creation wizard

**Goal**: 4-step wizard. Auto-saves DRAFT after each step. Go Live allowed with pending sources.

### D1 — Wizard route + layout

- [ ] `frontend/app/(dashboard)/agents/new/page.tsx` — replace existing simple form with wizard shell
- [ ] `frontend/components/wizard/WizardLayout.tsx` — step indicator (1→2→3→4), progress bar, Next/Back buttons
- [ ] Auto-save: on "Next" click, `PATCH /agents/{id}` — agent starts as DRAFT
- [ ] On first "Next" from Step 1: `POST /agents` → get `agent_id`, store in wizard state
- [ ] Browser refresh recovery: save `agent_id` to sessionStorage, reload wizard state from API

### D2 — Step 1: Basic Config

`frontend/components/wizard/Step1Config.tsx`

Fields:
- **Agent name** (required)
- **Description** — what does this agent help with? (short, shown in widget header)
- **Tone** — preset selector, 4 options (radio cards):
  - `Professional` — formal, precise, business language
  - `Friendly` — warm, conversational, approachable
  - `Casual` — relaxed, informal, uses contractions
  - `Empathetic` — supportive tone, suited for support/care contexts
- **Welcome message** — first message shown to user when widget opens (e.g. "Hi! How can I help you today?")
- **Fallback message** — shown when agent is paused or cannot answer (e.g. "I'm not able to help with that right now.")

No raw system prompt field. The system prompt is generated server-side from the tone preset + agent name + description. Template logic lives in `app/services/agent_service.py`:

```python
TONE_TEMPLATES = {
    "professional": "You are {name}, a professional AI assistant for {description}. "
                    "Respond formally, accurately, and concisely. ...",
    "friendly":     "You are {name}, a friendly AI assistant for {description}. "
                    "Be warm, approachable, and use a conversational tone. ...",
    "casual":       "You are {name}. Help users with {description}. "
                    "Keep it relaxed and natural. ...",
    "empathetic":   "You are {name}, a supportive AI assistant for {description}. "
                    "Show understanding, be patient, and acknowledge the user's situation. ...",
}
```

The generated system prompt is stored in `Agent.system_prompt` — users never see or edit the raw prompt in v1.

- [ ] Add `tone: AgentTone` enum field to `Agent` model (`professional|friendly|casual|empathetic`)
- [ ] `TONE_TEMPLATES` dict in `agent_service.py` — `generate_system_prompt(name, description, tone) -> str`
- [ ] `AgentCreate` schema: swap `system_prompt` field for `tone` + `description`
- [ ] On agent create/update: call `generate_system_prompt`, store result in `agent.system_prompt`
- [ ] React Hook Form + Zod validation
- [ ] Auto-save to API on Next

### D3 — Step 2: Knowledge Sources

`frontend/components/wizard/Step2Knowledge.tsx`

Three source types — tabs: **URL** | **Upload Files** | **Paste Text**

**URL sub-flow:**
1. Three inputs:
   - Root URL (required) — e.g. `https://example.com`
   - Path filter (optional) — e.g. `/docs` (only crawl pages under this path)
   - Page count (required) — numeric stepper, 1–20, default 10
2. Click "Start Crawling" → `POST /agents/{id}/knowledge/url` → source card appears immediately with `Pending` badge
3. Poll `GET /agents/{id}/knowledge/{id}/status` every 3s — badge cycles: `Pending → Crawling → Indexed`
4. Once `Indexed`: card expands to show crawled pages list (title + char count per page)
5. User reviews results — can:
   - **Remove** a page they don't want (calls `DELETE .../pages`)
   - **Add** a missing specific URL (calls `POST .../pages`, that page re-indexes independently)

**File upload:**
- Drag-and-drop zone, multi-file, accept `.pdf,.txt,.docx,.csv`
- POST `/agents/{id}/knowledge/upload` → status badge polling same as URL

**Text:**
- Textarea + title field → `POST /agents/{id}/knowledge/text` → instantly INDEXED (no async needed)

Source list shows all added sources with:
- Type icon (PDF / URL / Text)
- Status badge: `Pending` (gray) | `Processing` (yellow spinner) | `Indexed` (green) | `Failed` (red)
- Delete button

- [ ] Link discovery UI with checkbox list
- [ ] File drag-drop upload with progress
- [ ] Status polling hook `useKnowledgeStatus(knowledgeId)` — polls every 3s, stops on INDEXED/FAILED
- [ ] Source list component with live status badges

### D4 — Step 3: Tools & Model

`frontend/components/wizard/Step3Tools.tsx`

- Model selector: GPT-4o / GPT-4o Mini / Claude 3.5 Sonnet (radio cards)
- Temperature slider (0.0 → 1.0)
- Tools toggle list: Web Search, Lead Catcher, Weather (on/off)
- Max messages per session input

### D5 — Step 4: Deploy

`frontend/components/wizard/Step4Deploy.tsx`

**"Go Live" button** — enabled even if sources still indexing.
If any source is PENDING/PROCESSING: show yellow banner:
> "Agent is live with partial knowledge — 2 sources still indexing. Full knowledge available when complete."

**Channel cards:**

**Website Widget** (available immediately):
- Show embed code snippet
- Copy button
- Preview (mini widget mockup)

**WhatsApp** (requires pairing):
- "Connect WhatsApp" button → opens pairing modal
- Shows QR code from Baileys service
- Status: Disconnected / Scanning / Connected
- Once connected: shows connected number

**Other channels** (Slack, Discord): "Coming soon" badge

- [ ] Go Live button calls `POST /agents/{id}/deploy`
- [ ] Embed code display + copy
- [ ] WhatsApp pairing modal with QR code polling

---

## Phase E: WhatsApp — Baileys microservice

**Goal**: Separate Node.js service. Manages WhatsApp Web sessions. Bridges messages to FastAPI.

### Architecture

```
User's WhatsApp → Baileys WS connection → Node.js service
                                              ↓ POST /api/v1/channels/whatsapp/message
                                          FastAPI (chat engine)
                                              ↓ reply text
                                          Baileys sends reply → User's WhatsApp
```

### E1 — Node.js service setup

Location: `services/whatsapp/`

```
services/whatsapp/
├── package.json          (baileys, express, ioredis, axios)
├── src/
│   ├── index.ts          express app entry
│   ├── baileys.ts        Baileys session manager
│   ├── sessions.ts       per-user session store (Redis)
│   └── bridge.ts         POST to FastAPI, return reply
```

- [ ] `npm init` + install: `@whiskeysockets/baileys`, `express`, `ioredis`, `axios`, `qrcode`
- [ ] Session storage: save Baileys auth state to Redis key `wa_session:{user_id}`
- [ ] One session per user (their connected WhatsApp number)
- [ ] QR code generation: when user initiates pairing, generate QR, store in Redis `wa_qr:{user_id}` with 60s TTL

### E2 — Pairing API (internal endpoints on Node service)

```
POST /sessions/start    { user_id, agent_id }  → starts session, generates QR
GET  /sessions/qr       { user_id }            → returns QR code (base64 PNG or string)
GET  /sessions/status   { user_id }            → { status: "disconnected"|"scanning"|"connected", phone: "..." }
POST /sessions/stop     { user_id }            → disconnect + delete session
```

- [ ] `src/sessions.ts` — in-memory + Redis session map
- [ ] `src/index.ts` — Express routes for above
- [ ] QR polling: client polls `GET /sessions/qr` every 3s until `status == "connected"`

### E3 — Message bridge

When Baileys receives a message from WhatsApp:
1. Look up `agent_id` mapped to this `user_id` (stored in Redis when session started)
2. POST to FastAPI:
```json
POST /api/v1/channels/whatsapp/message
{
  "agent_id": "uuid",
  "sender_phone": "+1234567890",
  "message": "Hello, I need help",
  "user_id": "owner_user_id"
}
```
3. FastAPI runs chat engine (session_identifier = sender_phone)
4. Returns `{ "reply": "..." }`
5. Baileys sends reply back to sender

- [ ] `src/bridge.ts` — `forwardToFastAPI(agentId, senderPhone, message, userId)`
- [ ] Handle FastAPI errors gracefully (send "Agent unavailable" to user)
- [ ] Rate limit: max 10 messages/min per sender phone

### E4 — FastAPI WhatsApp channel endpoint

New endpoint in `app/api/v1/channels.py`:

```
POST /channels/whatsapp/message
Internal-only (verify via shared secret header X-Internal-Secret)
Body: { agent_id, sender_phone, message, user_id }
→ runs chat_engine.process_message(agent_id, message, session_identifier=sender_phone, channel="whatsapp")
→ returns { reply }
```

- [ ] `app/api/v1/channels.py` — new router
- [ ] Shared secret auth (env var `INTERNAL_SECRET`)
- [ ] Register router in `main.py`
- [ ] Test: channel endpoint processes message, returns reply, rejects missing secret

### E5 — Frontend pairing flow

`frontend/components/WhatsAppConnect.tsx`

1. Click "Connect WhatsApp" → call Baileys service `POST /sessions/start`
2. Modal opens showing QR code image (poll `/sessions/qr` every 3s)
3. User scans with WhatsApp → status changes to "connected"
4. Modal shows: "✓ Connected — +1234567890"
5. Store `{ whatsapp_connected: true, phone: "..." }` on agent record

- [ ] QR code display in modal
- [ ] Status polling until connected
- [ ] Connected state shown in Step 4 deploy panel
- [ ] Disconnect button

### E6 — Docker setup for Baileys service

```yaml
# docker/docker-compose.yml addition
whatsapp_service:
  build: ./services/whatsapp
  ports:
    - "3001:3001"
  environment:
    - REDIS_URL=redis://redis:6379
    - FASTAPI_URL=http://backend:8000
    - INTERNAL_SECRET=${INTERNAL_SECRET}
  depends_on: [redis]
  volumes:
    - whatsapp_sessions:/app/sessions
```

- [ ] `services/whatsapp/Dockerfile`
- [ ] Add to `docker-compose.yml`
- [ ] Add `INTERNAL_SECRET` and `WHATSAPP_SERVICE_URL` to `.env.example`

---

## Phase F: Website widget JS

**Goal**: Embeddable vanilla JS widget. No framework deps, <30KB.

### F1 — Widget script

Location: `frontend/public/widget.js` (or served from backend static files)

```html
<script
  src="https://your-domain.com/widget.js"
  data-agent-id="abc123"
  data-theme="light"
  data-position="bottom-right">
</script>
```

Widget JS responsibilities:
- Inject floating button (bottom-right)
- On click: open chat iframe or inline div
- POST to `/api/v1/widget/{agent_id}/chat`
- Manage `session_id` in localStorage
- Show `welcome_message` on open
- Display message history for session

- [ ] `frontend/public/widget.js` — self-contained IIFE, no React
- [ ] Floating button + chat panel CSS (injected via JS)
- [ ] Session ID stored in `localStorage` key `btlx_session_{agent_id}`
- [ ] API calls to configurable `data-api-url` (defaults to botlixio.com)
- [ ] Theme: light / dark (CSS variables)
- [ ] Position: bottom-right / bottom-left

### F2 — Embed code endpoint (already exists, verify)

`GET /agents/{id}/embed-code` — returns the `<script>` snippet with the correct `agent_id`.

- [ ] Verify embed code endpoint returns correct snippet
- [ ] Add `data-api-url` attribute pointing to backend

---

## Build order

```
A (model migration)
  → B (ARQ task queue)
    → C (crawler 2-phase)
      → D (frontend wizard)  ← can start D1/D2 in parallel with C
  → E (Baileys service)      ← independent, can build in parallel with C/D
  → F (widget JS)            ← independent from E, can build after D5
```

Phases A + B are hard prerequisites. Everything else can be parallelised.

---

## What this does NOT include (intentional v1 scope cuts)

- Slack / Discord channels (v2)
- Recursive full-site crawl (v2, capped at 20 pages from root)
- Billing / Stripe (separate phase)
- Re-crawl scheduling / stale detection (v2)
- BYOK (bring your own API key) (v2)
