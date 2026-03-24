---
name: feature-plan
description: >
  Entry point to the TDD pipeline — takes a new requirement, idea, or feature request and
  turns it into a formal feature doc (docs/features/) plus adds tasks to the implementation
  plan (docs/implementation-phases.md). Does NOT write specs or tests — hands off to
  spec-writer after. Use this skill whenever the user has a new feature idea, wants to add
  a requirement, plan a new capability, or define what to build next. Trigger on: "new feature",
  "add a feature", "I want to build X", "plan a feature", "add requirement", "feature plan",
  "define a feature", "I need to add X", "let's build X", "what would it take to add X".
---

# Feature Plan — Define a Feature & Update the Plan

Takes a feature idea and produces up to four outputs:
1. A **feature doc** at `docs/features/{NN}-{feature}.md`
2. **New routes** appended to `docs/api-routes.md` (only if the feature adds endpoints)
3. **New rules** appended to `docs/business-rules.md` (only if the feature adds rules)
4. **New tasks** added to the correct phase in `docs/implementation-phases.md`

This is the entry point to the pipeline. After this skill, the flow is:
```
/feature-plan → /spec-writer → /tdd-plan → /tdd-generate → /tdd-implement
```

## Input

`$ARGUMENTS` — one of:
- Feature name + description: `"notifications — send in-app and email notifications when events happen"`
- Just a name: `"notifications"` (will ask the user for requirements)
- `(empty)` — ask the user what they want to build

If the description is vague, ask clarifying questions before proceeding. You need enough detail to identify: what the feature does, who it's for, and what data/endpoints it needs.

---

## Step 1 — Read project context

Read these in parallel to understand what exists and where the new feature fits:

- `docs/implementation-phases.md` — current plan, phases, what's done
- `docs/business-rules.md` — subscription tiers, limits, access rules
- `docs/database-schema.md` — existing data model
- `docs/api-routes.md` — existing API surface
- `docs/features/` — list existing feature docs to find the next number and avoid overlap

Understand where the project is today (which phases are complete, which are in progress) so you place new tasks in the right phase.

---

## Step 2 — Identify scope and dependencies

Before writing anything, work out:

1. **Dependencies** — which existing features/phases must be complete first? (e.g., a notification feature depends on auth + agents being built)
2. **Which phase** — does this belong in an existing phase, or does it need a new one? Place it after its dependencies.
3. **Overlap check** — is this already partially covered by an existing feature doc? If so, tell the user and ask whether to extend the existing doc or create a new one.
4. **Scope boundaries** — what's in v1 vs deferred. Keep the first version focused.

State your findings before proceeding. Example:
```
This feature depends on Phase 2 (Auth) and Phase 4 (Agents).
It fits as a new Phase XX after Phase Y.
No overlap with existing feature docs.
```

---

## Step 3 — Write the feature doc

Create `docs/features/{NN}-{feature-name}.md` where `{NN}` is the next sequential number.

Use this structure (match the style of existing feature docs like `01-authentication.md`):

```markdown
# {Feature Name}

## Overview

{2-3 sentences: what this feature does and why it matters to users.}

---

## Data Model

See [database-schema.md](../database-schema.md) → `{Model}` model.

Key fields:
- `field_name`: description
- ...

{If new tables are needed, describe them here. Include field names, types, and purpose.
Note: this is a design sketch — the spec-writer will formalize it.}

---

## Pages

### `/{route}` — {Page Name}
- UI element / behavior
- ...

{List each frontend page/view this feature needs. Skip if backend-only.}

---

## API Endpoints

### `METHOD /api/v1/{resource}`
- Purpose
- Auth required: yes/no
- Request body / query params
- Response format
- Error cases

{List each endpoint. Keep it concise — spec-writer will expand these.}

---

## Business Rules

- {Rule 1: e.g., "Free plan: max 10 notifications/day"}
- {Rule 2: e.g., "Only verified users can enable notifications"}
- ...

---

## Dependencies

- {Feature/phase this depends on}
- ...

---

## Deferred (v2+)

- {Things explicitly out of scope for v1}
- ...
```

Adapt the template to fit the feature — not every section applies to every feature. Skip sections that don't make sense (e.g., "Pages" for a backend-only feature). But keep the same heading style as existing feature docs.

---

## Step 4 — Update project docs (only if needed)

After writing the feature doc, check whether it introduces new API endpoints or new business rules. **Skip this step entirely** if neither applies.

### If the feature adds new API endpoints → update `docs/api-routes.md`

1. Find the right section in `api-routes.md` (or create a new `## {Feature}` section)
2. Append the new routes using the existing table format:
   ```markdown
   | Method | Route | Description | Auth |
   |--------|-------|-------------|------|
   | POST | `/api/v1/...` | Description | User |
   ```
3. Match the style of existing sections exactly — same column order, same auth labels (`Public`, `User`, `Owner`, `Admin`)

### If the feature adds new business rules → update `docs/business-rules.md`

1. Find the right numbered section (or create a new `## {N}. {Topic}` section at the end)
2. Append the new rules using the existing style — prose + pseudocode blocks where appropriate
3. If the feature adds plan-based limits, update the plan comparison table in section 1

### Do NOT update these docs:
- `docs/database-schema.md` — updated during implementation when models are actually created
- `docs/folder-structure.md` — updated during implementation when files are actually created

---

## Step 5 — Update the implementation plan

Add tasks to `docs/implementation-phases.md`:

1. **Find the right phase** — either an existing phase or a new one
2. **If new phase**: insert it in dependency order with a `## Phase {N}: {Name}` header, goal description, and tasks
3. **If existing phase**: append tasks to the end of that phase's task list
4. **Task format**: match the existing style exactly:
   ```
   - [ ] `app/path/file.py` — Brief description of what to implement
   - [ ] Test: description of what to test
   ```
5. **Include both implementation and test tasks** — every implementation task should have a corresponding test task
6. **Update "Done when"** if adding to an existing phase

If adding a new phase causes renumbering of later phases, update the phase numbers.

---

## Step 6 — Summary

Print a summary to the conversation:

```
## Feature Planned: {Feature Name}

**Feature doc**: docs/features/{NN}-{feature}.md
**Plan updated**: Phase {N} in docs/implementation-phases.md
**Docs updated**: {list which docs were updated, or "none — no new routes or rules"}

**Tasks added:**
- [ ] task 1
- [ ] task 2
- ...

**Dependencies**: {list or "none — can start immediately"}

**Next step**: Run `/spec-writer {feature}` to create the detailed spec.
```

---

## Gotchas

- This skill creates the feature doc and updates the plan — it does NOT write specs, tests, or code. That's what the rest of the pipeline is for.
- Don't invent business rules — if the user hasn't specified pricing/limits, ask or mark as TBD.
- Don't add tasks to phases that are already marked complete unless the user explicitly asks to extend them.
- If a feature is large, suggest splitting it into multiple phases rather than cramming everything into one.
- Match the numbering and style of existing feature docs exactly — look at what's already in `docs/features/` before creating yours.
- New database tables should be described in the feature doc but NOT added to `database-schema.md` yet — that happens during implementation.
- Only update `api-routes.md` and `business-rules.md` if the feature actually adds new endpoints or rules — skip Step 4 entirely for internal/backend-only changes.

---

## Rules

- Always read the existing plan and feature docs before writing anything
- Respect dependency order — never place tasks before their dependencies
- Do NOT write specs — that's `/spec-writer`'s job
- Do NOT write tests or code — that's the TDD pipeline
- Do NOT modify `database-schema.md`, `folder-structure.md`, or any source code
- Ask clarifying questions if the feature idea is too vague to plan
- After writing, tell the user: "Run `/spec-writer {feature}` to create the detailed spec."
