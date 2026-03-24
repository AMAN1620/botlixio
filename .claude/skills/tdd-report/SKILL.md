---
name: tdd-report
description: >
  Runs pytest and produces a structured HTML test report with pass/fail counts,
  failure analysis, and prioritized fix suggestions. Distinguishes RED-phase
  ImportErrors (expected when implementation doesn't exist yet) from real bugs.
  Saves report as HTML file and prints a brief summary to the conversation.
  Use when the user wants to run tests and get a summary, check test status,
  or verify the RED/GREEN phase. Trigger on: "run tests", "test report",
  "tdd report", "are my tests passing", "what's failing", "run pytest",
  or when the user wants to see test results after generating or implementing.
---

# TDD Report — Run Tests, Generate HTML Report, Summarize

Run pytest, generate a visual HTML report file, and print a brief summary to the conversation.

## Input

`$ARGUMENTS` — optional filter:

| Argument | What gets tested |
|---|---|
| (empty) | All tests: `python -m pytest` |
| `<path>` | Specific file or directory |
| `<feature>` | e.g., `auth` → `python -m pytest -k "auth"` |

---

## Step 1 — Discover test configuration

```bash
cat pytest.ini 2>/dev/null || grep -A10 "\[tool.pytest" pyproject.toml 2>/dev/null
find . -type d -name "tests" | head -5
```

---

## Step 2 — Run the tests

Use the script at [scripts/run-tests.sh](scripts/run-tests.sh) or run directly:

```bash
cd backend && python -m pytest --tb=short -v $FILTER 2>&1
```

Capture the full output — you need every line for analysis.

---

## Step 3 — Classify each failure

For every failed test, classify it:

| Category | How to identify | What it means |
|----------|----------------|---------------|
| **RED phase** | `ImportError` or `ModuleNotFoundError` for a module that doesn't exist yet | Expected — implementation hasn't been written. TDD is working correctly. |
| **Setup error** | Fixture failure, DB connection error, missing env var | Infrastructure problem — not a code bug |
| **Real failure** | `AssertionError`, wrong status code, unexpected exception | Actual bug in implementation or test |

---

## Step 4 — Generate the HTML report

Use the template at [assets/report.html](assets/report.html). Read the template file, then replace all `__*_PLACEHOLDER__` tokens with the actual test data.

### Placeholder reference

| Placeholder | Replace with |
|---|---|
| `__DATE_PLACEHOLDER__` | Current date and time (e.g., `2026-03-23 10:45`) |
| `__FILTER_PLACEHOLDER__` | What was tested (e.g., `All tests`, `tests/unit/`, `-k "auth"`) |
| `__PASSED_PLACEHOLDER__` | Number of passed tests |
| `__FAILED_PLACEHOLDER__` | Number of failed tests |
| `__SKIPPED_PLACEHOLDER__` | Number of skipped tests |
| `__ERRORS_PLACEHOLDER__` | Number of error tests |
| `__RATE_PLACEHOLDER__` | Pass rate as percentage (e.g., `85%`) |
| `__PHASE_BANNER_PLACEHOLDER__` | Phase banner HTML (see below) |
| `__RED_SECTION_PLACEHOLDER__` | RED phase failures section HTML or empty string |
| `__REAL_SECTION_PLACEHOLDER__` | Real failures section HTML or empty string |
| `__SETUP_SECTION_PLACEHOLDER__` | Setup errors section HTML or empty string |
| `__RECOMMENDATIONS_PLACEHOLDER__` | Recommendations section HTML or empty string |

### Phase banner HTML

Use one of these based on the TDD phase assessment:

```html
<!-- RED phase -->
<div class="phase-banner red">RED PHASE — N tests fail with ImportError. Implementation not written yet. This is expected.</div>

<!-- GREEN phase -->
<div class="phase-banner green">GREEN PHASE — All tests pass. Ready to refactor.</div>

<!-- MIXED -->
<div class="phase-banner mixed">MIXED — N pass, N fail with real errors. Fix failures below.</div>
```

### RED section HTML

```html
<div class="section" id="section-red">
  <div class="section-header">
    <span>RED Phase Failures (expected)</span>
    <span class="count">N</span>
  </div>
  <div class="section-body">
    <table>
      <thead><tr><th>Test</th><th>Missing Module / Function</th></tr></thead>
      <tbody>
        <tr><td class="mono">test_file.py::TestX::test_y</td><td class="mono">app.module.function</td></tr>
        <!-- repeat for each RED failure -->
      </tbody>
    </table>
  </div>
</div>
```

### Real failures section HTML

```html
<div class="section" id="section-real">
  <div class="section-header">
    <span>Real Failures (bugs)</span>
    <span class="count">N</span>
  </div>
  <div class="section-body">
    <div class="failure-card">
      <div class="test-name">test_file.py::TestX::test_y</div>
      <dl class="detail">
        <dt>Error</dt><dd>AssertionError: expected 200, got 404</dd>
        <dt>Cause</dt><dd>Route not registered in router</dd>
        <dt>Fix</dt><dd>Add the route to app/api/v1/router.py</dd>
      </dl>
    </div>
    <!-- repeat for each real failure -->
  </div>
</div>
```

### Setup errors section HTML

```html
<div class="section" id="section-setup">
  <div class="section-header">
    <span>Setup Errors</span>
    <span class="count">N</span>
  </div>
  <div class="section-body">
    <div class="failure-card">
      <div class="test-name">Fixture / config issue name</div>
      <dl class="detail">
        <dt>Error</dt><dd>Error message</dd>
        <dt>Impact</dt><dd>Causes N test(s) to fail</dd>
        <dt>Fix</dt><dd>How to resolve</dd>
      </dl>
    </div>
  </div>
</div>
```

### Recommendations section HTML

```html
<div class="section">
  <div class="section-header"><span>Recommendations</span></div>
  <div class="section-body">
    <ol class="rec-list">
      <li><span class="rec-num">1</span><span>Fix setup errors first — they cascade</span></li>
      <li><span class="rec-num">2</span><span>Fix real failures</span></li>
      <li><span class="rec-num">3</span><span>Implement code to turn RED tests GREEN</span></li>
    </ol>
  </div>
</div>
```

### Omit empty sections

If a category has zero items, **omit that section entirely** — replace the placeholder with an empty string. Do not render empty tables.

---

## Step 5 — Write the HTML file and print summary

1. **Write the report** to `docs/tdd/reports/tdd-report-{date}.html` (e.g., `tdd-report-2026-03-23.html`). Create `docs/tdd/reports/` if it doesn't exist.

2. **Print a brief summary** to the conversation — just the key numbers and the phase. Use this exact format:

```
## Test Report — {date}

| Passed | Failed | Skipped | Errors | Pass Rate |
|--------|--------|---------|--------|-----------|
| N      | N      | N       | N      | N%        |

**Phase**: {RED / GREEN / MIXED} — {one-line explanation}

Report saved to `docs/tdd/reports/tdd-report-{date}.html`
```

That's all that goes in the conversation. The HTML file has the full detail.

---

## Gotchas

- In RED phase, **all tests should fail** with `ImportError`. If some tests pass during RED phase, something is wrong — the implementation may already exist or the test isn't importing correctly.
- `conftest.py` fixture failures cascade — one broken fixture can cause dozens of test failures. Identify the root fixture and report it once, not once per test.
- If pytest can't collect tests at all (syntax error in test file), the output looks different from normal failures. Check for `ERROR collecting` in the output.
- `pytest-asyncio` warnings about missing `asyncio_mode` are noisy but harmless. Don't report them as issues.
- Count carefully — pytest's summary line (`X passed, Y failed`) is authoritative. Don't recount manually.
- Read the HTML template file before generating — do not hardcode the template in your response.

---

## Rules

- Run tests in the backend directory (or wherever pytest.ini points)
- Do NOT modify any test or implementation files — this is diagnostic only
- Do NOT re-run tests in a loop hoping they pass — run once, analyze, report
- Always include the pass rate percentage
- Group failures by category (RED phase / Setup / Real) so the user knows what to fix vs what's expected
- Always write an HTML report file — never skip the file output
- Keep the conversation summary short — the detail is in the HTML
