# Admin Panel

## Overview

The Admin Panel provides platform-level management capabilities. Only users with `role = ADMIN` can access these endpoints. It covers user management, platform API key management, analytics, pricing configuration, and tool/channel management.

---

## Pages

### `/admin` — Admin Dashboard
- KPI cards: Total users, Active agents, Messages today, Revenue this month
- Growth charts: User signups, message volume over time
- System health: API response time, error rate

### `/admin/users` — User Management
- Table: Name, Email, Role, Plan, Agents count, Messages used, Status, Last login
- Search by name/email
- Actions: Block/unblock, change role, view detail
- Filter by role, plan, status

### `/admin/api-keys` — Platform API Keys
- List of configured LLM provider keys: Provider, Key name, Last 4 digits, Status
- "Add Key" button → modal: Provider, Key name, API key
- Delete/deactivate key
- Keys are encrypted at rest; full key never shown after creation

### `/admin/pricing` — Pricing Configuration
- Editable table of plan configurations:
  | Field | Description |
  |-------|-------------|
  | Plan name | Display name |
  | Monthly price | In cents |
  | Yearly price | In cents |
  | Max agents | Limit |
  | Max messages/month | Limit |
  | Max knowledge items | Per agent |
  | Max workflows | Limit |
  | Allowed models | Multi-select |
  | Allowed tools | Multi-select |
  | Features | JSONB (BYOK, priority support, etc.) |
  | Stripe Price ID (monthly) | For checkout |
  | Stripe Price ID (yearly) | For checkout |

### `/admin/analytics` — Platform Analytics
- User growth chart (daily signups over 30/90/365 days)
- Message volume chart (daily messages)
- Plan distribution pie chart
- Top agents by message count
- Revenue breakdown by plan
- Agent model usage distribution

---

## Admin Endpoints

### User Management

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/admin/users` | List all users (paginated, searchable) |
| GET | `/api/v1/admin/users/{id}` | User detail with agents, subscription |
| PUT | `/api/v1/admin/users/{id}` | Update role, active status |
| POST | `/api/v1/admin/users/{id}/block` | Block user (is_active=false) |

### Platform API Keys

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/admin/api-keys` | List keys (masked) |
| POST | `/api/v1/admin/api-keys` | Add new key (encrypted) |
| DELETE | `/api/v1/admin/api-keys/{id}` | Delete key |

### Pricing

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/admin/pricing` | Get all plan configs |
| PUT | `/api/v1/admin/pricing` | Bulk update pricing |

### Analytics

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/admin/analytics` | Aggregated platform stats |

Query params: `?period=30d|90d|1y`

### Tools & Channels

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/admin/tools` | List tool configs |
| POST | `/api/v1/admin/tools` | Create tool |
| PUT | `/api/v1/admin/tools/{id}` | Update tool |
| DELETE | `/api/v1/admin/tools/{id}` | Delete tool |
| GET | `/api/v1/admin/channels` | List channel configs |
| POST | `/api/v1/admin/channels` | Create channel |
| PUT | `/api/v1/admin/channels/{id}` | Update channel |
| DELETE | `/api/v1/admin/channels/{id}` | Delete channel |

---

## Authorization

```python
# Dependency for admin routes
async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Applied to admin router
router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])
```

---

## API Key Security

```python
# Adding a key
async def add_api_key(provider: str, key_name: str, api_key: str):
    encrypted = encrypt_credentials({"key": api_key}, settings.FERNET_KEY)
    record = PlatformAPIKey(
        provider=provider,
        key_name=key_name,
        encrypted_key=encrypted,
    )
    # Full key never stored in plaintext
    # Only last 4 chars shown in UI

# Using a key
async def get_api_key(provider: str) -> str:
    record = await repo.get_active_key(provider)
    decrypted = decrypt_credentials(record.encrypted_key, settings.FERNET_KEY)
    return decrypted["key"]
```

---

## Analytics Queries

```python
# Example aggregations
async def get_analytics(period: str) -> dict:
    return {
        "total_users": await count_users(),
        "total_agents": await count_agents(),
        "messages_today": await count_messages_today(),
        "messages_this_month": await count_messages_this_month(),
        "revenue_this_month": await sum_revenue_this_month(),
        "user_signups": await daily_signups(period),
        "message_volume": await daily_messages(period),
        "plan_distribution": await count_by_plan(),
        "top_agents": await top_agents_by_messages(limit=10),
        "model_usage": await count_by_model(),
    }
```

---

## Business Rules

1. **Admin-only access**: All admin endpoints require `role == ADMIN`
2. **API key encryption**: Keys encrypted with Fernet at rest, never logged
3. **Key masking**: UI shows only last 4 characters of API keys
4. **Pricing isolation**: Pricing changes don't affect existing subscriptions until renewal
5. **User blocking**: Blocked users can't log in; their agents still respond (to not break deployed widgets)
6. **Self-protection**: Admin cannot block themselves or change their own role
