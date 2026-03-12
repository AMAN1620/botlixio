# Chat Engine

## Overview

The Chat Engine is the core LLM pipeline that processes messages, manages conversation sessions, injects knowledge context, handles tool calling, and tracks usage. It powers both the authenticated API chat and the public widget.

---

## Data Model

See [database-schema.md](../database-schema.md) → `ChatSession`, `ChatMessage` models.

Key fields:
- `ChatSession`: Links agent to a conversation context (IP, phone, user ID)
- `ChatMessage`: Individual messages with role, content, token count, tool data
- `response_time_ms`: Latency tracking per message

---

## Message Processing Pipeline

```
1. Receive message (user content + agent_id + session_identifier)
2. ─── Session Management ───
   a. Find existing session (agent_id + session_identifier)
   b. If no session → create new session
   c. If session exists but inactive (>24h) → create new session
3. ─── Plan Check ───
   a. Check subscription.messages_used < plan.max_messages_per_month
   b. If exceeded → return PlanLimitExceeded error
4. ─── Build Context ───
   a. Load last N messages from session (e.g., last 20)
   b. Load agent's knowledge base content
   c. Build system prompt: agent.system_prompt + knowledge context + tool instructions
5. ─── LLM Call ───
   a. Call LiteLLM.acompletion() with:
      - model: agent.model
      - messages: [system_prompt, ...history, user_message]
      - tools: agent's enabled tools (if any)
      - temperature: agent.temperature
      - max_tokens: agent.max_tokens
   b. Pass API key: platform key OR user's BYOK key
6. ─── Tool Loop (if tool calls returned) ───
   a. For each tool call: dispatch to tool registry → execute → get result
   b. Add tool call + result to message history
   c. Call LLM again with updated history
   d. Repeat until no tool calls OR max 5 iterations
7. ─── Save & Track ───
   a. Save user ChatMessage (role: "user")
   b. Save assistant ChatMessage (role: "assistant", token_count, response_time_ms)
   c. Increment subscription.messages_used
   d. Increment agent.total_messages
   e. Update session.message_count, session.last_message_at
8. ─── Lead Check ───
   a. If lead_catcher tool enabled: scan response for [LEAD_DATA] token
   b. If found: parse JSON → save Lead → strip token from displayed response
9. ─── Return ───
   Return ChatResponse { message, session_id, token_count }
```

---

## Session Management

### Session Identification
| Channel | session_identifier |
|---------|--------------------|
| Widget | Client IP address |
| WhatsApp | Phone number |
| Discord | Discord user ID |
| Slack | Slack user ID |
| Test Chat | Authenticated user ID |

### Session Expiry
- Sessions auto-expire after 24 hours of no messages
- Expired sessions are marked `is_active = false`
- New message after expiry creates a fresh session

### History Window
- Load last 20 messages for context (configurable)
- System prompt + history + knowledge must fit within model's context window
- If too long: truncate oldest history messages first

---

## Knowledge Context Injection

```python
def build_system_prompt(agent, knowledge_items) -> str:
    base = agent.system_prompt
    
    if knowledge_items:
        knowledge_text = "\n\n".join([k.content for k in knowledge_items])
        # Truncate to fit context window
        max_knowledge_chars = 50_000  # ~12.5k tokens
        if len(knowledge_text) > max_knowledge_chars:
            knowledge_text = knowledge_text[:max_knowledge_chars] + "\n[Content truncated]"
        
        base += f"\n\n--- Knowledge Base ---\n{knowledge_text}"
    
    return base
```

---

## LLM Client Abstraction

```python
# app/services/llm_client.py

class LLMClient:
    """Wrapper around LiteLLM for testability."""
    
    async def chat_completion(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        api_key: str | None = None,  # BYOK override
    ) -> dict:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )
        return response
```

---

## API Key Resolution

```
1. Check if user has a BYOK key for the agent's provider
   → If yes AND plan allows BYOK: use user's key
2. Otherwise: use platform API key for the provider
   → Look up active PlatformAPIKey for agent.provider
   → Decrypt with Fernet
3. If no key available: return error "No API key configured for {provider}"
```

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Agent is PAUSED | Return fallback message, no LLM call |
| Agent is DRAFT | Return 404 (not accessible) |
| Message limit exceeded | Return 429 with "Monthly message limit reached" |
| LLM API error | Return generic "Something went wrong" + log error |
| LLM timeout (>30s) | Return "Response took too long" + log |
| Empty message | Return 400 "Message cannot be empty" |
| Very long message (>10k chars) | Truncate to 10k chars before sending |
| Tool execution error | Pass error to LLM, let it respond gracefully |
| Max tool iterations reached | Return last LLM response without further tool calls |

---

## Business Rules

1. **Message counting**: Every user message counts as 1 message (tool calls don't count extra)
2. **Token tracking**: Total tokens from LLM response stored per message
3. **History preservation**: Messages are never deleted, only sessions can be cleared
4. **Concurrency**: Multiple concurrent sessions per agent are supported
5. **Rate limiting**: Widget: 10 msg/min per IP; Auth API: 30 msg/min per user

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/v1/chat/{agent_id}` | Send message, get reply |
| GET | `/api/v1/chat/{agent_id}/sessions` | List chat sessions |
| GET | `/api/v1/chat/{agent_id}/sessions/{session_id}` | Get session messages |
| DELETE | `/api/v1/chat/{agent_id}/sessions/{session_id}` | Clear session |
