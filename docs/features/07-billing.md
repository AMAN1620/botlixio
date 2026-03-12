# Billing & Subscriptions

## Overview

Stripe-powered subscription billing with four plans (Free, Starter, Growth, Business). Plan limits are enforced at the service layer. The billing module handles Stripe Checkout sessions, webhook events, and subscription lifecycle management.

---

## Data Model

See [database-schema.md](../database-schema.md) → `Subscription`, `PricingConfig` models.

Key fields:
- `Subscription`: User's current plan, Stripe IDs, usage counters
- `PricingConfig`: Admin-managed plan definitions with limits and pricing

---

## Plans

| Feature | Free | Starter ($19/mo) | Growth ($49/mo) | Business ($149/mo) |
|---------|------|----------|--------|----------|
| Agents | 1 | 3 | 10 | Unlimited |
| Messages/month | 100 | 1,000 | 10,000 | 100,000 |
| Knowledge items/agent | 5 | 20 | 50 | Unlimited |
| Workflows | 0 | 3 | 10 | Unlimited |
| BYOK | ❌ | ❌ | ✅ | ✅ |

Prices define in `PricingConfig` table, managed by admin. Above are default values.

---

## Pages

### `/billing` — Billing Page
- Current plan card with usage meters (agents, messages, knowledge)
- Plan comparison table with upgrade/downgrade buttons
- "Manage Billing" button → Stripe Customer Portal
- Billing history from Stripe

---

## Subscription Lifecycle

```
1. User signs up → FREE plan (no Stripe customer)
2. User clicks "Upgrade" → POST /api/v1/billing/checkout
   → Create Stripe Checkout Session
   → Redirect to Stripe hosted page
3. User completes payment → Stripe fires `checkout.session.completed`
   → Webhook creates/updates Subscription record
   → Set plan, stripe_customer_id, stripe_subscription_id
4. Monthly renewal → Stripe fires `invoice.paid`
   → Extend current_period_end
   → Reset messages_used to 0
5. User downgrades → effective at period end
   → cancel_at_period_end = true
   → When period ends: update plan to new lower plan
6. User cancels → cancel_at_period_end = true
   → When period ends: downgrade to FREE
7. Payment fails → Stripe fires `invoice.payment_failed`
   → Set status = PAST_DUE
   → Stripe handles retry (3 attempts)
   → After all retries fail → `customer.subscription.deleted`
   → Downgrade to FREE
```

---

## Stripe Webhook Events

| Event | Handler Action |
|-------|---------------|
| `checkout.session.completed` | Create/update subscription, set plan |
| `invoice.paid` | Extend period, reset monthly usage |
| `invoice.payment_failed` | Set status to PAST_DUE |
| `customer.subscription.updated` | Sync plan changes (up/downgrade) |
| `customer.subscription.deleted` | Downgrade to FREE, clear Stripe IDs |

### Webhook Security
```python
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
    # Process event...
```

---

## Downgrade Rules

When downgrading to a lower plan:

```
1. Excess agents (count > new plan.max_agents):
   → PAUSED (not deleted)
   → User must manually delete or upgrade to re-enable

2. Excess knowledge items:
   → Items remain but user cannot add more
   → Knowledge still works in chat

3. Excess workflows:
   → PAUSED
   → User must delete to within limits

4. Model restrictions:
   → If agent uses a model not in new plan:
   → Agent continues working until next edit
   → On edit: must change to an allowed model

5. BYOK:
   → If downgrading from BYOK-eligible plan:
   → BYOK keys remain but stop being used
   → Platform keys used instead
```

---

## Monthly Message Reset

```python
# Runs on first API call each month (or via cron)
async def check_message_reset(subscription: Subscription):
    now = datetime.utcnow()
    if subscription.messages_reset_at is None or \
       subscription.messages_reset_at.month < now.month:
        subscription.messages_used = 0
        subscription.messages_reset_at = now
```

---

## Edge Cases

| Scenario | Expected Behaviour |
|----------|-------------------|
| Free user tries to checkout | Show plan comparison, redirect to Stripe |
| User already on plan tries to subscribe again | Redirect to Stripe Portal |
| Webhook received twice (idempotent) | Check subscription already updated, skip |
| User's card expires | Stripe handles retry, webhook fires on failure |
| Admin changes pricing | Existing subscribers keep their rate until next renewal |

---

## Business Rules

1. **One subscription per user**: Enforced by unique constraint on `user_id`
2. **Message reset**: Monthly on the 1st or first API call of the month
3. **Downgrade at period end**: Never immediately revoke access
4. **Webhook idempotency**: Process each event exactly once
5. **Pricing changes**: Don't affect existing subscribers until renewal
6. **Free plan**: Always available, no Stripe involvement

---

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/v1/billing/plans` | List available plans (public) |
| GET | `/api/v1/billing/subscription` | Get user's subscription |
| POST | `/api/v1/billing/checkout` | Create Stripe checkout session |
| POST | `/api/v1/billing/portal` | Create Stripe billing portal |
| POST | `/api/v1/billing/cancel` | Cancel subscription |
| POST | `/api/v1/billing/webhook` | Stripe webhook handler |
