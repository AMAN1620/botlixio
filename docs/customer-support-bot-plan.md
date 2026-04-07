# Customer Support Bot — Build Plan
**Scope**: Ship a working "Customer Support" solution end-to-end.
User registers → adds website URL + documents → bot is trained → gets embed code → pastes it on their site.

---

## Stack Decisions (locked for this plan)

| Layer | Choice | Reason |
|---|---|---|
| Web scraping | **Crawl4AI** | Async, LLM-friendly chunking, handles SPAs |
| Vector DB | **Qdrant** (local Docker) | Fast, free, no cloud needed to start |
| Embeddings | **OpenAI `text-embedding-3-small`** | Cheap, high quality |
| LLM | **OpenAI `gpt-4o-mini`** | Fast + cheap for support use-case |
| Widget | Vanilla JS snippet | Zero dependency, copy-paste into any site |

---

## Step 1 — Verify Auth Works in Docker

**Goal**: `docker compose up` → all tests green → auth endpoints live at `localhost:8000`.

### 1.1 Fix / verify Docker environment
- [ ] Confirm `.env` has all required vars: `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- [ ] Ensure `backend/Dockerfile` installs dev deps (needed to run alembic migrations inside container)
- [ ] Add `RESEND_API_KEY=test` and `FERNET_KEY=<generated>` placeholders so config loads without error

### 1.2 Run and validate
- [ ] `docker compose -f docker/docker-compose.yml up -d` — all 3 services healthy
- [ ] `alembic upgrade head` runs inside backend container (migrations apply)
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /api/v1/auth/register` creates a user
- [ ] `POST /api/v1/auth/login` returns access + refresh tokens
- [ ] `GET /api/v1/auth/me` returns user with valid Bearer token
- [ ] Run full test suite: `python -m pytest -x -v` — all pass

### 1.3 Add Qdrant to docker-compose
- [ ] Add `qdrant` service to `docker/docker-compose.yml` (port 6333)
- [ ] Add `QDRANT_URL=http://qdrant:6333` to `.env.example`
- [ ] Add `QDRANT_URL` to `app/core/config.py`

---

## Step 2 — Agent CRUD (Phase 4 of main plan)

**Goal**: User can create a "Customer Support" agent — gives it a name, persona, welcome message.

### 2.1 Backend
- [ ] `app/schemas/agent.py` — `AgentCreate`, `AgentUpdate`, `AgentResponse`
  - Fields: `name`, `description`, `solution_type` (enum: `customer_support`, …), `persona`, `welcome_message`, `status`
- [ ] `app/repositories/agent_repo.py` — `create`, `get_by_id`, `get_by_user`, `update`, `soft_delete`
- [ ] `app/services/agent_service.py` — create (plan limit check), update, delete, deploy/pause
- [ ] `app/api/v1/agents.py` — `POST /agents`, `GET /agents`, `GET /agents/{id}`, `PATCH /agents/{id}`, `DELETE /agents/{id}`, `POST /agents/{id}/deploy`, `POST /agents/{id}/pause`
- [ ] Register router in `app/main.py`

### 2.2 Tests (write FIRST — TDD)
- [ ] `tests/unit/test_agent_service.py` — create, limit check, update, delete
- [ ] `tests/integration/test_agent_api.py` — all endpoints, ownership, 401/403

---

## Step 3 — Knowledge Base: URL Scraping with Crawl4AI

**Goal**: User pastes their website URL → Crawl4AI scrapes it → content chunked → stored in Qdrant.

### 3.1 New dependencies
- [ ] Add to `pyproject.toml`: `crawl4ai`, `qdrant-client`, `openai`, `tiktoken`
- [ ] `app/core/qdrant.py` — Qdrant client singleton, `ensure_collection(agent_id)` helper

### 3.2 Document parsing & chunking
- [ ] `app/services/document_parser.py` — extract text from PDF, TXT, DOCX, CSV (PyPDF2, python-docx)
- [ ] `app/services/chunker.py` — split text into ~512-token chunks with 50-token overlap (tiktoken)

### 3.3 Crawl4AI scraper
- [ ] `app/services/crawler.py`
  - `crawl_url(url: str) -> list[str]` — uses Crawl4AI `AsyncWebCrawler`, returns cleaned text chunks
  - Handles: single page, sitemap-based multi-page (max 50 pages for free tier)
  - Strips nav/footer boilerplate

### 3.4 Embedding & vector storage
- [ ] `app/services/embedder.py`
  - `embed_chunks(chunks: list[str]) -> list[list[float]]` — OpenAI `text-embedding-3-small`
  - `upsert_to_qdrant(agent_id, chunks, embeddings)` — stores with metadata `{agent_id, source_url, chunk_index}`

### 3.5 Knowledge API
- [ ] `app/schemas/knowledge.py` — `KnowledgeSourceCreate`, `KnowledgeSourceResponse`
  - `source_type`: `url` | `pdf` | `txt` | `docx` | `csv` | `text`
- [ ] `app/repositories/knowledge_repo.py` — CRUD for knowledge source records (tracks what was ingested)
- [ ] `app/services/knowledge_service.py`
  - `add_url(agent_id, url)` → crawl → chunk → embed → upsert → save record
  - `add_document(agent_id, file)` → parse → chunk → embed → upsert → save record
  - `add_text(agent_id, text)` → chunk → embed → upsert → save record
  - `delete_source(source_id)` → delete Qdrant vectors by source filter
  - `list_sources(agent_id)` → return all sources with status
- [ ] `app/api/v1/knowledge.py`
  - `POST /agents/{id}/knowledge/url` — submit URL, returns job status
  - `POST /agents/{id}/knowledge/upload` — multipart file upload
  - `POST /agents/{id}/knowledge/text` — raw text
  - `GET /agents/{id}/knowledge` — list sources
  - `DELETE /agents/{id}/knowledge/{source_id}`
- [ ] Register router in `app/main.py`

### 3.6 Tests
- [ ] `tests/unit/test_chunker.py` — chunk sizes, overlap
- [ ] `tests/unit/test_knowledge_service.py` — mock Crawl4AI + Qdrant, test each source type
- [ ] `tests/integration/test_knowledge_api.py` — upload, scrape, list, delete

---

## Step 4 — Chat Engine with RAG

**Goal**: Widget sends a message → retrieve relevant chunks from Qdrant → build prompt → GPT-4o-mini answers.

### 4.1 Backend
- [ ] `app/services/llm_client.py` — OpenAI async wrapper (chat completion, testable/mockable)
- [ ] `app/schemas/chat.py` — `ChatRequest`, `ChatResponse`
- [ ] `app/repositories/chat_repo.py` — `ChatSession` + `ChatMessage` CRUD
- [ ] `app/services/retriever.py`
  - `retrieve(agent_id, query, top_k=5)` → embed query → Qdrant similarity search → return top chunks
- [ ] `app/services/chat_engine.py`
  1. Find/create session (keyed by `agent_id` + `session_id` from widget)
  2. Check agent is LIVE
  3. Load last 10 messages (history)
  4. `retrieve()` top 5 chunks for the query
  5. Build system prompt: agent persona + knowledge context
  6. Call `llm_client.chat()` with history + system prompt
  7. Save assistant message
  8. Return response
- [ ] `app/api/v1/chat.py` (public, no auth required)
  - `GET /widget/{agent_id}/status` — returns agent name, welcome message, is_live
  - `POST /widget/{agent_id}/chat` — `{session_id, message}` → `{reply, session_id}`

### 4.2 Tests
- [ ] `tests/unit/test_retriever.py` — mock Qdrant, test top-k retrieval
- [ ] `tests/unit/test_chat_engine.py` — mock LLM + retriever, test full pipeline
- [ ] `tests/integration/test_widget_api.py` — widget endpoints, rate limiting

---

## Step 5 — Embed Code Generator

**Goal**: After agent is LIVE, dashboard shows a JS snippet user can copy-paste into any website.

### 5.1 Backend
- [ ] `app/api/v1/agents.py` addition — `GET /agents/{id}/embed-code`
  - Returns the JS snippet as a string (not a file)
  - Snippet hardcodes the `agent_id` and points to `FRONTEND_URL`

### 5.2 Widget JS (static file, served by frontend)
- [ ] `frontend/public/widget.js` — self-contained vanilla JS widget
  - Creates a floating chat button (bottom-right corner)
  - Opens a chat panel on click
  - Calls `GET /widget/{agent_id}/status` on load (shows welcome message)
  - Calls `POST /widget/{agent_id}/chat` on message send
  - Stores `session_id` in `localStorage`
  - Styled with inline CSS (zero external dependencies)
  - ~200 lines total

### 5.3 Embed snippet format
```html
<!-- Botlixio Widget -->
<script>
  window.BotlixioAgentId = "YOUR_AGENT_ID";
  window.BotlixioApiUrl = "https://your-api.botlixio.com";
</script>
<script src="https://your-domain.com/widget.js" async></script>
```

### 5.4 Dashboard UI
- [ ] `frontend/app/(dashboard)/agents/page.tsx` — agent list page
- [ ] `frontend/app/(dashboard)/agents/new/page.tsx` — create agent form (name, persona, welcome message)
- [ ] `frontend/app/(dashboard)/agents/[id]/page.tsx` — agent detail page
  - Tabs: Overview | Knowledge | Embed Code | Test Chat
- [ ] `frontend/app/(dashboard)/agents/[id]/knowledge/page.tsx` — add URL / upload file / add text
- [ ] `frontend/app/(dashboard)/agents/[id]/embed/page.tsx` — copy embed snippet + live preview
- [ ] `frontend/lib/api.ts` — Axios instance with auth interceptors
- [ ] `frontend/stores/agent-store.ts` — Zustand store for agent state

---

## Step 6 — Test Chat in Dashboard

**Goal**: Dashboard has a "Test Chat" panel that lets the owner preview their bot before going live.

- [ ] `frontend/components/TestChatPanel.tsx` — embeds the widget pointed at current agent
- [ ] Add to agent detail page under "Test Chat" tab
- [ ] No backend changes needed (reuses widget API)

---

## Delivery Checklist

When all steps above are done, the user journey is:

1. **Register** → verify email → **login**
2. **Create agent** → name it "Customer Support Bot", set persona
3. **Add knowledge** → paste website URL → Crawl4AI scrapes it → chunks stored in Qdrant
4. **Deploy** → agent status → `LIVE`
5. **Get embed code** → copy JS snippet
6. **Paste** into any website `<body>` → chat widget appears
7. Visitor asks question → RAG retrieves relevant chunks → GPT-4o-mini answers

---

## File Change Summary

### New backend files
```
backend/app/core/qdrant.py
backend/app/services/crawler.py          ← Crawl4AI
backend/app/services/chunker.py
backend/app/services/embedder.py
backend/app/services/retriever.py
backend/app/services/llm_client.py
backend/app/services/chat_engine.py
backend/app/services/document_parser.py
backend/app/services/knowledge_service.py
backend/app/services/agent_service.py
backend/app/schemas/agent.py
backend/app/schemas/knowledge.py
backend/app/schemas/chat.py
backend/app/repositories/agent_repo.py
backend/app/repositories/knowledge_repo.py
backend/app/repositories/chat_repo.py
backend/app/api/v1/agents.py
backend/app/api/v1/knowledge.py
backend/app/api/v1/chat.py
```

### New frontend files
```
frontend/public/widget.js
frontend/lib/api.ts
frontend/stores/agent-store.ts
frontend/app/(dashboard)/agents/page.tsx
frontend/app/(dashboard)/agents/new/page.tsx
frontend/app/(dashboard)/agents/[id]/page.tsx
frontend/app/(dashboard)/agents/[id]/knowledge/page.tsx
frontend/app/(dashboard)/agents/[id]/embed/page.tsx
frontend/components/TestChatPanel.tsx
```

### Modified files
```
docker/docker-compose.yml               ← add Qdrant service
backend/app/core/config.py              ← add QDRANT_URL, OPENAI_API_KEY (already there)
backend/app/main.py                     ← register new routers
backend/pyproject.toml                  ← add crawl4ai, qdrant-client, tiktoken
.env.example                            ← add QDRANT_URL
```

---

## Order of Execution

```
Step 1 → Docker + Auth verified
Step 2 → Agent CRUD (backend + tests)
Step 3 → Knowledge ingestion (Crawl4AI + Qdrant)
Step 4 → Chat engine (RAG + LLM)
Step 5 → Embed code + Widget JS
Step 6 → Dashboard UI (agents list, create, knowledge, embed, test)
```

Each step is independently testable. Do NOT skip TDD — write failing tests before implementation.
