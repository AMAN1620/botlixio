---
description: Pick and execute the next incomplete task using TDD
---

# Execute Next

You are a senior full-stack developer working on the Botlixio project using **TDD (Test-Driven Development)**. Your job is to identify the next incomplete task from the implementation plan, write tests FIRST, then implement the feature to make those tests pass.

## Input

Arguments: $ARGUMENTS

Supported arguments:
- (empty) — pick the next task automatically based on dependency order
- `phase 2` / `phase 3` / etc. — work within a specific phase
- `redo <target>` — re-implement a completed task

## Process

### Step 1: Read the plan and identify next task

Read these files (in parallel):
- `docs/implementation-phases.md` — the master plan with `[x]`/`[ ]` checkboxes

Then determine the **next incomplete task** by following these rules:
1. Find the earliest phase that has unchecked `[ ]` tasks
2. Within that phase, pick the first unchecked task
3. Verify all dependencies are satisfied (earlier phases done)

### Step 2: Ensure SPEC.md exists, then read context

Before writing any code:
- **If SPEC.md exists** → read it and proceed
- **If SPEC.md does NOT exist** → check for feature doc at `docs/features/{NN}-*.md`
  - If feature doc exists → use `/create-spec` workflow to generate SPEC.md first
  - If no feature doc (utility/config task) → skip SPEC.md

Read relevant docs: `docs/business-rules.md`, `docs/api-routes.md`, `docs/database-schema.md`

### Step 3: TDD — Write tests FIRST

#### 3a: Generate test cases from spec
If SPEC.md exists and no test plan yet → derive test cases

#### 3b: Write test code

For Python backend:
- **Unit tests**: `backend/tests/unit/test_{feature}.py`
  - Pure functions, Pydantic schemas, utility functions
  - Use pytest, no mocks needed for pure functions
  
- **Service tests**: `backend/tests/unit/test_{feature}_service.py`
  - Mock repositories, test business logic
  
- **API tests**: `backend/tests/integration/test_{feature}_api.py`
  - Use httpx.AsyncClient, mock services
  - Test auth, validation, response shapes

#### 3c: Verify tests fail (RED phase)
```bash
cd backend && python -m pytest tests/unit/test_{feature}.py -v
```
Tests SHOULD fail at this point.

### Step 4: Implement the feature (GREEN phase)

Write the minimum code to make tests pass:
- Follow conventions in `docs/tech-stack.md`
- Use existing patterns from the codebase
- Proper Python type hints — no `Any` unless necessary

Validate:
```bash
cd backend && python -m pytest tests/unit/test_{feature}.py -v
```
Fix until all tests pass.

### Step 5: Refactor

Quick review — remove duplication, ensure naming consistency. Tests must still pass.

### Step 6: Update the implementation plan

After task is complete:
1. Edit `docs/implementation-phases.md` — change `[ ]` to `[x]`
2. If entire phase is done, note it

### Step 7: Run plan check

After the batch is complete, use `/plan-check` to verify consistency.

## Batch execution

Default: batch 2-4 related tasks per run. Run full TDD cycle for each.

## Rules

- **TDD is mandatory for all logic.** Write tests first. No exceptions.
- **Respect dependency order.** Never skip ahead.
- **Read before writing.** Always read existing files before modifying.
- **Don't over-engineer.** Build exactly what's needed.
- **Validate before marking done.** Tests must pass to mark `[x]`.
