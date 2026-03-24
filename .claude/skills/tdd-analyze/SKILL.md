---
name: tdd-analyze
description: >
  Analyzes coverage gaps between a SPEC.md and its TEST-CASES.md. Maps every
  spec requirement to test cases and finds: uncovered requirements, weakly
  covered ones, and orphaned tests with no matching spec requirement. Use after
  tdd-plan has produced a TEST-CASES.md. Trigger on: "analyze coverage",
  "find test gaps", "coverage gap analysis", "tdd analyze", "what's missing
  from my test plan", or when the user has a TEST-CASES.md and wants to verify
  completeness.
---

# TDD Analyze — Coverage Gap Analysis

Map every spec requirement to test cases. Find what's missing, what's weak, and what's orphaned.

## Input

`$ARGUMENTS` — path to a SPEC.md file. The TEST-CASES.md must exist in `docs/tdd/` (produced by `tdd-plan`).

If no path given, ask the user.

---

## Step 1 — Locate the files

```bash
# Find the spec and its test cases
ls "$SPEC_PATH" 2>/dev/null
ls docs/tdd/*.TEST-CASES.md 2>/dev/null
```

The SPEC lives in `docs/specs/`, the TEST-CASES lives in `docs/tdd/`. Extract the feature name from the spec filename (e.g., `auth` from `auth.SPEC.md`) and look for `docs/tdd/{feature}.TEST-CASES.md`.

If TEST-CASES.md doesn't exist, tell the user to run `/tdd-plan` first and stop.

---

## Step 2 — Read both files completely

Read the SPEC.md and TEST-CASES.md in full. Do not start analysis until both are fully loaded.

---

## Step 3 — Assign spec references

Walk through the spec and tag every testable requirement with a ref:

```
SPEC-{SECTION}-{NNN}
```

Examples: `SPEC-AUTH-001`, `SPEC-BILLING-003`, `SPEC-EDGE-012`

A "testable requirement" is any statement that describes observable behavior: what the system does, returns, rejects, or stores.

---

## Step 4 — Map requirements to test cases

For each `SPEC-*` ref, find the test case(s) in TEST-CASES.md that cover it.

A test case "covers" a requirement only if it:
- Sends input that exercises the stated behavior
- Asserts the exact outcome the spec describes (not just "no error")

Classify each mapping:

| Status | Meaning |
|--------|---------|
| **Covered** | Test case fully verifies the requirement |
| **Weakly covered** | Test exists but doesn't fully verify (e.g., checks status code but not response body) |
| **Uncovered** | No test case for this requirement |

---

## Step 5 — Find orphaned tests

Check each test case in TEST-CASES.md. If it doesn't map to any `SPEC-*` requirement, flag it as **Orphaned**. Orphaned tests aren't necessarily wrong — they may cover implicit requirements — but they should be reviewed.

---

## Step 6 — Assign risk levels

| Risk | Criteria |
|------|----------|
| **Critical** | Auth, permissions, billing, data integrity gaps |
| **High** | Core CRUD flows, business rule enforcement |
| **Medium** | Error messages, validation edge cases |
| **Low** | Cosmetic behavior, nice-to-have coverage |

---

## Step 7 — Write COVERAGE-ANALYSIS.md

Output to `docs/tdd/`:
- Input: `docs/specs/auth.SPEC.md` → Output: `docs/tdd/auth.COVERAGE-ANALYSIS.md`

Create `docs/tdd/` if it doesn't exist.

Use the template from [template.md](template.md) for the exact output format.

---

## Gotchas

- "Weakly covered" is the hardest to judge. A test that checks `status_code == 200` but ignores the response body is weak if the spec defines what the body should contain.
- Don't flag framework-default validations (like Pydantic's `min_length`) as uncovered unless the spec explicitly calls them out.
- Business rules from `docs/business-rules.md` are P0 requirements even if they only appear in the business rules doc, not the feature spec.
- Orphaned tests may be valid — flag them for review, don't recommend deletion outright.

---

## Rules

- Read both files completely before starting analysis
- Do NOT modify the spec or TEST-CASES.md — this is a diagnostic skill
- Do NOT write test code — only the analysis document
- Be strict about what "covered" means — a test that calls a function but doesn't assert the stated outcome is not coverage
