# Integrations & Workflows

## Overview

Integrations connect Botlixio to third-party services (Telegram, Gmail, Slack, Notion). Workflows are user-defined automations that trigger on events (new lead, new message) and execute a sequence of integration actions.

---

## Data Model

See [database-schema.md](../database-schema.md) → `UserIntegration`, `Workflow`, `WorkflowStep`, `WorkflowExecution` models.

---

## Part A: Integrations

### Supported Providers

| Provider | Auth Method | Available Actions |
|----------|-----------|-------------------|
| Telegram | Bot Token | Send message to chat |
| Gmail | OAuth2 / App password | Send email |
| Slack | OAuth2 / Webhook URL | Send message to channel |
| Notion | API Token | Create page, update database |

### Pages

#### `/integrations` — Integration Management
- Grid of integration cards: Provider name, logo, status (Connected/Disconnected)
- "Connect" button → modal with credential input
- "Disconnect" button for connected integrations
- "Test" button → POST to test endpoint

### Connect Flow

```
1. User selects provider
2. Enters credentials (token, API key, or OAuth redirect)
3. POST /api/v1/integrations/{provider}/connect
4. Backend:
   a. Validate credentials (make test API call)
   b. Encrypt credentials with Fernet
   c. Store encrypted in UserIntegration
   d. Return success
5. Show "Connected ✓" status
```

### Credential Security

```python
# app/utils/encryption.py

from cryptography.fernet import Fernet

def encrypt_credentials(data: dict, key: str) -> str:
    f = Fernet(key.encode())
    json_str = json.dumps(data)
    return f.encrypt(json_str.encode()).decode()

def decrypt_credentials(encrypted: str, key: str) -> dict:
    f = Fernet(key.encode())
    json_str = f.decrypt(encrypted.encode()).decode()
    return json.loads(json_str)
```

---

## Part B: Workflows

### Workflow Structure

A workflow consists of:
1. **Trigger**: Event that starts the workflow
2. **Steps**: Ordered list of actions to execute (1-10 steps)
3. **Status**: DRAFT / ACTIVE / PAUSED

### Available Triggers

| Trigger | Description | Event Data |
|---------|-------------|-----------|
| `new_lead` | New lead captured | Lead object |
| `new_message` | New chat message received | Message object |
| `agent_deployed` | Agent status changed to LIVE | Agent object |

### Pages

#### `/workflows` — Workflow List
- Table: Name, Trigger, Steps count, Status, Last executed, Executions count
- "Create Workflow" button
- Status toggle (Active/Paused)

#### `/workflows/[id]` — Workflow Detail

Tabbed layout:

| Tab | Content |
|-----|---------|
| Builder | Trigger selector + step list (drag & reorder) |
| Executions | History table with status, timestamps |
| Settings | Name, description, status |

### Workflow Builder

**Step 1: Select Trigger**
- Dropdown: new_lead, new_message, agent_deployed
- Trigger config (e.g., for new_lead: which agent)

**Step 2: Add Steps**
Each step:
| Field | Type | Notes |
|-------|------|-------|
| Integration | Select | From connected integrations |
| Action | Select | Available actions for selected provider |
| Config | Dynamic form | Action-specific fields |

Example steps:
```
Trigger: new_lead (Agent: Support Bot)
Step 1: [Gmail] Send email to sales@company.com
        Subject: "New lead from {lead.name}"
        Body: "Email: {lead.email}, Phone: {lead.phone}"
Step 2: [Slack] Post message to #leads channel
        Message: "🎯 New lead: {lead.name} ({lead.email})"
Step 3: [Notion] Add row to Leads database
        Properties: Name={lead.name}, Email={lead.email}
```

### Workflow Execution Engine

```python
# app/services/workflow_engine.py

async def execute_workflow(workflow: Workflow, trigger_data: dict):
    execution = await create_execution(workflow.id, trigger_data)
    
    for step in workflow.steps:
        try:
            # Get integration credentials
            integration = await get_user_integration(
                workflow.user_id, step.integration_provider
            )
            credentials = decrypt_credentials(integration.credentials_encrypted)
            
            # Execute action
            result = await integration_registry.dispatch(
                provider=step.integration_provider,
                action=step.action,
                config=step.config,
                credentials=credentials,
                context=trigger_data,
            )
            
            execution.results[step.order] = result
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            break
    else:
        execution.status = ExecutionStatus.COMPLETED
    
    execution.completed_at = datetime.utcnow()
    await save_execution(execution)
```

### Execution Rules
- Steps execute sequentially (step 1 → 2 → 3)
- If any step fails, execution stops (no partial rollback)
- Timeout: 30 seconds per step
- Retries: Up to 3 retries with exponential backoff per step
- Execution history retained for 90 days

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Integration disconnected during workflow | Execution fails at that step |
| Credentials expired / revoked | Execution fails with "Authentication error" |
| Step timeout | Retry up to 3 times, then mark failed |
| Circular trigger (workflow triggers itself) | Not possible — workflows only trigger on events, not on workflow completion |
| Workflow with no steps | Allowed but does nothing |
| Plan limit exceeded | Cannot create more workflows |

---

## Business Rules

1. **Integration ownership**: Each user manages their own integrations
2. **Credential encryption**: Always encrypted at rest with Fernet
3. **Workflow plan limits**: Free: 0, Starter: 3, Growth: 10, Business: unlimited
4. **Execution logging**: All executions logged with full results and errors
5. **Step limit**: Max 10 steps per workflow
6. **Template substitution**: Step configs support `{variable.field}` syntax for trigger data

---

## API Endpoints

### Integrations
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/integrations` | List connected integrations |
| POST | `/api/v1/integrations/{provider}/connect` | Connect integration |
| DELETE | `/api/v1/integrations/{provider}/disconnect` | Disconnect |
| POST | `/api/v1/integrations/{provider}/test` | Test credentials |

### Workflows
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/workflows` | List workflows |
| POST | `/api/v1/workflows` | Create workflow |
| GET | `/api/v1/workflows/{id}` | Get workflow detail |
| PUT | `/api/v1/workflows/{id}` | Update workflow |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow |
| POST | `/api/v1/workflows/{id}/activate` | Activate |
| POST | `/api/v1/workflows/{id}/pause` | Pause |
| GET | `/api/v1/workflows/{id}/executions` | Execution history |
