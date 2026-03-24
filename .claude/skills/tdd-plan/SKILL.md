---
name: tdd-plan
description: >
  Extracts structured test cases from a SPEC.md file. Reads the spec completely,
  identifies every testable requirement (happy flows, edge cases, API contracts,
  schema validations, business rules), and writes a TEST-CASES.md file. Use when
  the user wants to plan tests from a spec, extract test cases, or start the TDD
  pipeline. Trigger on: "plan tests for X", "extract test cases", "what tests do
  I need for this spec", "tdd plan", or when a SPEC.md is shared and the user
  asks how to test it.
---

# TDD Plan — Extract Test Cases from Spec

Read a SPEC.md and produce a structured TEST-CASES.md with every testable requirement.

## Input

`$ARGUMENTS` — path to a SPEC.md file (e.g., `docs/specs/auth.SPEC.md`).

If no path given, ask the user which spec to plan from.

---

## Step 1 — Discover project layout

```bash
find . -type d -name "tests" | head -5
cat pytest.ini 2>/dev/null || grep -A5 "\[tool.pytest" pyproject.toml 2>/dev/null
ls backend/app/ 2>/dev/null || ls app/ 2>/dev/null || ls src/ 2>/dev/null
```

Use discovered paths throughout — never hardcode.

---

## Step 2 — Read the spec completely

Read the entire SPEC.md in one pass. Do not start extracting until you have read every line. Partial reads cause missed requirements.

---

## Step 3 — Extract test cases

Walk through the spec section by section and extract:

1. **Happy flows** — one test case per observable outcome
2. **Edge cases** — one test case per boundary condition or table row
3. **API contracts** — one test case per endpoint x response code
4. **Schema validations** — focus on custom validators and conditional logic (skip framework defaults like `min_length` unless the spec explicitly calls them out)
5. **Business rules** — one test case per stated rule

### Layer assignment

| Prefix | Layer | What it tests |
|--------|-------|---------------|
| `UNIT` | Unit | Pure functions, no dependencies |
| `SVC` | Service | Service method with mocked repository |
| `API` | API/Integration | HTTP endpoint via test client |

### Priority assignment

| Priority | Criteria |
|----------|----------|
| P0 | Auth, security, billing, data integrity |
| P1 | Core business flows (create, update, delete) |
| P2 | Validation edge cases, cosmetic, nice-to-have |

---

## Step 4 — Write TEST-CASES.md

Write the output to `docs/tdd/`, named after the spec's feature:
- Input: `docs/specs/auth.SPEC.md` → Output: `docs/tdd/auth.TEST-CASES.md`

Create `docs/tdd/` if it doesn't exist.

Use the template from [template.md](template.md) for the exact output format.

For a real example of expected output, see [examples/sample.md](examples/sample.md).

---

## Gotchas

- A test case must be **verifiable** — "system works correctly" is not a test case. State the exact assertion.
- Don't create test cases for framework behavior (e.g., "Pydantic rejects missing required field") unless the spec explicitly defines custom validation logic for that field.
- If the spec references `docs/business-rules.md`, read it too — business rules generate P0 test cases.
- Count your test cases per layer and verify the summary table matches. Off-by-one errors here cause confusion downstream.
- The spec is the source of truth. If something seems wrong in the spec, note it but still generate the test case as written.

---

## Rules

- Read the spec completely before extracting anything
- Do NOT write implementation code or pytest files — only TEST-CASES.md
- Do NOT modify the spec
- Err toward more coverage for auth, billing, and data integrity (P0)
- Every test case must have: ID, priority, preconditions, steps, expected outcome
