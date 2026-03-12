# Business Rules

Core business logic governing access control, plan limits, chat engine behavior, and billing in Botlixio.

---

## 1. Subscription Plans & Limits

### Default Plan Configuration

| Feature | Free | Starter | Growth | Business |
|---------|------|---------|--------|----------|
| Agents | 1 | 3 | 10 | Unlimited |
| Messages/month | 100 | 1,000 | 10,000 | 100,000 |
| Knowledge items/agent | 5 | 20 | 50 | Unlimited |
| Workflows | 0 | 3 | 10 | Unlimited |
| Models | gpt-4o-mini only | + gpt-4o, claude-3-haiku | + claude-3.5-sonnet, gemini-pro | All models |
| Tools | Web search only | All tools | All tools | All tools |
| Channels | Widget only | + WhatsApp | + Discord, Slack | All channels |
| BYOK | No | No | Yes | Yes |
| Support | Community | Email | Priority | Dedicated |

### Limit Enforcement

```
Before creating agent:
  if user.subscription.agents_used >= plan.max_agents:
    raise PlanLimitExceeded("agent_limit")

Before sending message:
  if user.subscription.messages_used >= plan.max_messages_per_month:
    raise PlanLimitExceeded("message_limit")

Before adding knowledge:
  if agent.knowledge_items.count() >= plan.max_knowledge_items:
    raise PlanLimitExceeded("knowledge_limit")

Before creating workflow:
  if user.workflows.count() >= plan.max_workflows:
    raise PlanLimitExceeded("workflow_limit")
```

### Message Count Reset
- Messages reset on the 1st of each month at 00:00 UTC
- `subscription.messages_reset_at` tracks the last reset

### Model Access Control
- Each plan has an `allowed_models` list
- Before chat: verify `agent.model` is in the user's plan's `allowed_models`
- BYOK users can use any model supported by LiteLLM regardless of plan

---

## 2. Authentication & Security

### JWT Tokens
- **Access token**: 30 minutes expiry, contains `sub` (user ID), `role`, `exp`
- **Refresh token**: 7 days expiry, stored in httpOnly cookie
- **Refresh rotation**: Each refresh issues a new refresh token; old one is invalidated

### Password Rules
- Minimum 8 characters
- Hashed with bcrypt (passlib CryptContext)
- Never stored or logged in plaintext

### Email Verification
```
1. User registers → status: is_verified=false
2. Verification email sent with token (24h expiry)
3. User clicks link → POST /api/v1/auth/verify-email
4. Token validated → is_verified=true
5. Unverified users can log in but cannot create agents
```

### Password Reset
```
1. User requests reset → POST /api/v1/auth/forgot-password
2. Reset email sent with token (1h expiry)
3. User submits new password → POST /api/v1/auth/reset-password
4. Token validated → password updated, token invalidated
```

### OAuth Flow
- Google/GitHub/Apple OAuth supported
- On first OAuth login: create user with `auth_provider`, `oauth_id`, `is_verified=true`
- On subsequent OAuth login: match by `oauth_id` + `auth_provider`
- OAuth users have no `password_hash`

---

## 3. Agent Configuration

### Agent Status Lifecycle
```
DRAFT → LIVE (deploy action)
LIVE → PAUSED (pause action)
PAUSED → LIVE (resume action)
Any → DRAFT (only if no active sessions)
```

- Only `LIVE` agents respond to chat messages
- `PAUSED` agents return the fallback message
- `DRAFT` agents are not accessible via public endpoints

### System Prompt Construction
```
Final system prompt = [
  agent.system_prompt,
  "\n\n--- Knowledge Base ---\n",
  agent.knowledge_context,  # Injected RAG content
  "\n\n--- Instructions ---\n",
  tool_instructions,        # If tools are enabled
  lead_catcher_instructions # If lead catcher is enabled
]
```

### Default Values
- Temperature: 0.7
- Max tokens: 1024
- Model: gpt-4o-mini
- Welcome message: "Hello! How can I help you today?"
- Fallback message: "This agent is currently offline."

---

## 4. Chat Engine Rules

### Session Management
- Sessions identified by: `agent_id` + `session_identifier`
- Widget sessions: `session_identifier` = client IP address
- WhatsApp sessions: `session_identifier` = phone number
- Discord/Slack: `session_identifier` = platform user ID
- Sessions auto-expire after 24 hours of inactivity

### Message Processing Pipeline
```
1. Receive message
2. Find or create session
3. Check plan limits (message count)
4. Load conversation history (last N messages)
5. Build system prompt with knowledge context
6. Call LLM via LiteLLM
7. If tool calls in response → execute tools → feed results → repeat step 6
8. Save assistant message
9. Increment message counters (subscription + agent)
10. Check for lead data in response → save lead if found
11. Return response
```

### Tool Calling Loop
- Maximum 5 tool call iterations per message
- If max iterations reached, return last LLM response without tool calls
- Each tool call result is added to the message history
- Tool errors are passed to the LLM as error messages (not exposed to end user)

### Token Accounting
- Track `token_count` on each ChatMessage (from LLM usage response)
- Track `total_messages` on Agent (cumulative)
- Track `messages_used` on Subscription (monthly, resettable)

---

## 5. Knowledge Base (RAG)

### Content Sources
| Source | Processing |
|--------|-----------|
| PDF | Extract text via PyPDF2, store as plain text |
| TXT | Store as-is |
| CSV | Convert to readable text format |
| DOCX | Extract text via python-docx |
| URL | Fetch page → BeautifulSoup → extract main content |
| Raw text | Store as-is |

### Content Limits
- Max file size: 10 MB
- Max content per knowledge item: 100,000 characters
- Max total knowledge per agent: determined by plan
- URL scraping timeout: 30 seconds

### Context Injection
```
For each chat message:
  1. Get all knowledge items for the agent
  2. Concatenate content (truncate if needed to fit context window)
  3. Inject into system prompt before the main instructions

Note: v1 uses simple concatenation. v2 will add vector-based retrieval.
```

---

## 6. Lead Capture

### Lead Catcher Tool
When enabled on an agent, the system prompt includes instructions for the LLM to extract contact information using a special token format:

```
If the user shares contact information, output it in this format:
[LEAD_DATA]{"name":"...", "email":"...", "phone":"...", "company":"..."}[/LEAD_DATA]
```

### Lead Processing
```
1. After each LLM response, check for [LEAD_DATA] token
2. If found: parse JSON, save Lead record
3. Strip the [LEAD_DATA] token from the displayed response
4. Associate lead with agent_id and session_id
```

---

## 7. Billing & Stripe Integration

### Subscription Lifecycle
```
User signs up → FREE plan (no Stripe)
User upgrades → Stripe Checkout → webhook confirms → plan updated
User downgrades → effective at period end
User cancels → cancel_at_period_end = true, access until period end
Period ends without renewal → downgrade to FREE
Payment fails → status = PAST_DUE, 3 retry attempts
```

### Webhook Events to Handle
| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create/update subscription |
| `invoice.paid` | Extend subscription period |
| `invoice.payment_failed` | Set status to PAST_DUE |
| `customer.subscription.updated` | Sync plan changes |
| `customer.subscription.deleted` | Downgrade to FREE |

### Downgrade Rules
When downgrading to a lower plan:
- Excess agents are **paused** (not deleted)
- Excess knowledge items remain but cannot add more
- Excess workflows are **paused**
- User must manually reduce usage to within new limits to re-activate

---

## 8. Integrations & Credential Security

### Credential Storage
- Integration credentials encrypted with Fernet symmetric encryption
- Encryption key stored in environment (`FERNET_KEY`)
- Key validated at application startup; startup fails if invalid

### Credential Lifecycle
```
1. User connects integration → credentials encrypted → stored in DB
2. Workflow execution → decrypt credentials → use for API call → discard
3. User disconnects → credentials deleted from DB
```

### Integration Execution
- Each integration has a standard interface: `execute_action(action, config, credentials)`
- Timeout: 30 seconds per action
- Retries: 3 attempts with exponential backoff

---

## 9. Rate Limiting

### Public Endpoints (Widget)
| Endpoint | Rate Limit |
|----------|-----------|
| Widget chat | 10 messages/minute per IP |
| Widget status | 30 requests/minute per IP |

### Authenticated Endpoints
| Endpoint | Rate Limit |
|----------|-----------|
| Chat API | 30 messages/minute per user |
| Agent CRUD | 60 requests/minute per user |
| Knowledge upload | 10 uploads/minute per user |

---

## 10. Multi-Channel Message Normalization

### Incoming Message Format (Unified)
```python
{
    "channel": "whatsapp" | "discord" | "slack",
    "sender_id": "phone_number" | "discord_user_id" | "slack_user_id",
    "message": "text content",
    "agent_id": "uuid",
    "metadata": { ... }  # Channel-specific data
}
```

### Processing
```
1. Webhook receives channel-specific payload
2. Normalize to unified format
3. Look up agent by channel config
4. Process through chat engine (same as widget)
5. Send response back via channel-specific API
```

---

## 11. Data Immutability Rules

- **Chat messages**: Immutable once created (audit trail)
- **Lead records**: Can be updated but not deleted
- **Workflow executions**: Immutable (historical log)
- **Subscription changes**: All transitions logged
- **Agent deletions**: Soft-delete (set status, don't remove data)
