---
name: tdd-implement
description: >
  Picks the next incomplete task from the implementation plan and writes the minimum code
  to make failing tests pass (GREEN phase). Orchestrates existing TDD skills — checks for
  SPEC, TEST-CASES, and pytest files before writing code. Does not write tests from scratch;
  uses tdd-plan and tdd-generate if tests don't exist yet. Use this skill whenever the user
  wants to implement the next feature, write code to make tests pass, continue building the
  project, or move from RED to GREEN phase. Trigger on: "implement", "tdd implement",
  "execute next", "make tests pass", "write the code", "green phase", "next feature",
  "continue building", "keep going", "do the next thing".
---

# TDD Implement — Write Code to Make Tests Pass (GREEN Phase)

Picks the next task from the plan and writes the minimum implementation to turn RED tests GREEN.

## Input

`$ARGUMENTS`:

| Argument | Behaviour |
|---|---|
| (empty) | Auto-pick the next task by dependency order |
| `phase 2` | Work within a specific phase only |
| `{feature}` | Implement a specific feature (e.g., `agents`) |
| `redo {task}` | Re-implement a previously completed task |

---

## Step 1 — Find the next task

Read `docs/implementation-phases.md`. Pick by these rules:
1. Find the earliest phase with unchecked `[ ]` tasks
2. Within that phase, pick the first unchecked task
3. Verify all earlier phases are complete (no skipping ahead)

State which task you're implementing before doing anything else.

---

## Step 2 — Ensure prerequisites exist

Check for each artifact in order. If missing, tell the user which skill to run and stop.

```
1. SPEC exists?
   → Check: docs/specs/{feature}.SPEC.md
   → Missing: "Run /spec-writer {feature} first."

2. TEST-CASES exist?
   → Check: docs/tdd/{feature}.TEST-CASES.md
   → Missing: "Run /tdd-plan docs/specs/{feature}.SPEC.md first."

3. Pytest files exist?
   → Check: backend/tests/unit/test_{feature}.py
   → Missing: "Run /tdd-generate docs/tdd/{feature}.TEST-CASES.md first."
```

If all three exist, proceed.

---

## Step 3 — Verify RED phase

Run the tests to confirm they fail as expected:

```bash
cd backend && python -m pytest tests/unit/test_{feature}.py tests/integration/test_{feature}_api.py -v --tb=short 2>&1
```

Expected: tests fail with `ImportError` or `ModuleNotFoundError` (RED phase).

If tests already pass, the implementation may already exist. Tell the user and stop.

If tests fail with unexpected errors (not ImportError), flag the issue — the test files may need fixing before implementation.

---

## Step 4 — Read context before writing code

Read in parallel:
- The SPEC: `docs/specs/{feature}.SPEC.md` — schemas, endpoints, business rules
- The TEST-CASES: `docs/tdd/{feature}.TEST-CASES.md` — what exactly to implement
- The test files — understand what assertions to satisfy
- `docs/business-rules.md` — plan limit checks, access control rules
- `docs/database-schema.md` — model field reference
- Existing code in adjacent modules — match patterns and conventions

---

## Step 5 — Implement (GREEN phase)

Write the minimum code to make tests pass. No more, no less.

**File convention:**
```
backend/app/models/{feature}.py          ← SQLAlchemy model
backend/app/schemas/{feature}.py         ← Pydantic schemas
backend/app/repositories/{feature}_repo.py  ← data access
backend/app/services/{feature}_service.py   ← business logic
backend/app/api/v1/{feature}.py          ← route handlers
backend/app/api/v1/dependencies.py       ← DI providers (if needed)
```

**Follow conventions:**
- SQLAlchemy 2.0 `Mapped[]` syntax for models
- UUID primary keys
- Async everywhere (`async def`, `await`)
- Services depend on repositories, never on models directly
- Routes are thin — validate input, call service, return response
- Check plan limits in services before operations
- Verify resource ownership (`user_id` matches current user)

---

## Step 6 — Verify GREEN

Run the tests again:

```bash
cd backend && python -m pytest tests/unit/test_{feature}.py tests/integration/test_{feature}_api.py -v --tb=short 2>&1
```

All tests must pass. If any fail:
1. Read the failure output carefully
2. Fix the implementation (not the tests)
3. Re-run until GREEN

Then run the full test suite to check for regressions:

```bash
cd backend && python -m pytest -v --tb=short 2>&1
```

---

## Step 7 — Quick refactor

Review what you just wrote:
- Remove duplication
- Fix naming inconsistencies
- Ensure no business logic leaked into routes

Tests must stay GREEN throughout. Re-run after any refactor.

---

## Step 8 — Update the plan

Mark the completed task in `docs/implementation-phases.md`:
```
[x] Task description
```

If the entire phase is done, note it.

---

## Step 9 — Report

Print a brief summary to the conversation:

```
## Implemented: {task name}

**Files created/modified:**
- `backend/app/services/{feature}_service.py` (new)
- `backend/app/schemas/{feature}.py` (new)
- ...

**Tests:** N passed, 0 failed

**Next:** Run `/tdd-report` to generate a full HTML report, or `/tdd-implement` to continue.
```

---

## Gotchas

- Never write tests from scratch in this skill. Tests come from `/tdd-generate`. If they don't exist, stop and tell the user.
- If a test seems wrong (testing impossible behavior), flag it but don't modify the test. Tell the user to update the TEST-CASES.md and re-run `/tdd-generate`.
- Migration files: if you add/modify a model, create an alembic migration: `alembic revision --autogenerate -m "description"`. But review it before applying.
- Don't implement deferred items from the SPEC — only implement what's in the current task.
- Check `conftest.py` for existing fixtures — use them, don't duplicate.

---

## Rules

- Tests before code — never write implementation without existing failing tests
- If prerequisites (SPEC, TEST-CASES, pytest files) are missing, stop and guide the user
- Do NOT modify test files — fix implementation to match tests
- Do NOT skip phases — respect dependency order
- Minimum viable implementation — make tests pass, nothing more
- A task is only done when all its tests pass
- Always run the full suite after implementation to catch regressions
