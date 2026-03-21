---
name: execute-next
description: >
  Picks the next incomplete task from the implementation plan and executes it using TDD —
  writes failing tests first, then implements the minimum code to make them pass, then
  refactors. Use this skill whenever the user wants to continue building the project,
  implement the next feature, or run a TDD cycle. Trigger on: "execute next", "what
  should I build next", "implement the next task", "continue building", "next feature",
  "keep going", "do the next thing in the plan".
---

# Execute Next

Picks the next incomplete task from `docs/implementation-phases.md` and implements it
with full TDD: Red → Green → Refactor.

## Arguments

`$ARGUMENTS`:

| Argument | Behaviour |
|---|---|
| (empty) | Auto-pick the next task by dependency order |
| `phase 2` | Work within a specific phase only |
| `redo <task>` | Re-implement a previously completed task |

Default batch size: 2–4 related tasks per run.

---

## Step 1: Find the next task

Read `docs/implementation-phases.md`. Pick by these rules:
1. Find the earliest phase with unchecked `[ ]` tasks
2. Within that phase, pick the first unchecked task
3. Verify all earlier phases are complete (no skipping ahead)

---

## Step 2: Get the spec

Before writing any code:

- **SPEC.md exists** → read it and proceed
- **SPEC.md missing, feature doc exists** → run `/create-spec` first to generate it
- **No feature doc (utility/config task)** → skip SPEC.md, read relevant docs instead

Also read: `docs/business-rules.md`, `docs/api-routes.md`, `docs/database-schema.md`

---

## Step 3: Write tests FIRST (Red phase)

Never write implementation before tests. The tests must fail before you write code.

**Test file locations:**

| Test type | Path | What it tests |
|---|---|---|
| Unit | `backend/tests/unit/test_{feature}.py` | Pure functions, schemas, utils |
| Service | `backend/tests/unit/test_{feature}_service.py` | Business logic with mocked repos |
| API | `backend/tests/integration/test_{feature}_api.py` | Routes with mocked services |

**Verify RED:**
```bash
cd backend && python -m pytest tests/unit/test_{feature}.py -v
# Tests MUST fail here — if they pass, the test is wrong
```

---

## Step 4: Implement (Green phase)

Write the minimum code to make the tests pass. No more, no less.

File convention:
```
backend/app/models/{feature}.py       ← SQLAlchemy model
backend/app/schemas/{feature}.py      ← Pydantic schemas
backend/app/repositories/{feature}_repo.py  ← data access
backend/app/services/{feature}_service.py   ← business logic
backend/app/api/v1/{feature}.py       ← route handlers
```

**Verify GREEN:**
```bash
cd backend && python -m pytest tests/unit/test_{feature}.py tests/integration/test_{feature}_api.py -v
# All tests must pass before moving on
```

Follow conventions:
- SQLAlchemy 2.0 `Mapped[]` syntax for models
- UUID primary keys
- Async everywhere (`async def`, `await`)
- Services depend on repositories, never on models directly
- Routes are thin — validate input, call service, return response

---

## Step 5: Refactor

Quick review only — remove duplication, fix naming. Tests must stay green throughout.

```bash
cd backend && python -m pytest -v  # full suite
```

---

## Step 6: Update the plan

Mark the completed task:
```bash
# In docs/implementation-phases.md, change [ ] to [x]
```

If the entire phase is done, note it in the plan.

---

## Step 7: Run a consistency check

After completing a batch of tasks:
- Run `/plan-check` to verify implementation matches the plan
- Run `/docs-sync schema` to verify model changes are reflected in schema docs

---

## Rules

- TDD is non-negotiable — tests before code, every time
- Read existing files before modifying anything
- Don't over-engineer — build exactly what the spec and tests require
- Respect dependency order — never start Phase N+1 work while Phase N has incomplete tasks
- A task is only done when all its tests pass — don't mark `[x]` until green
