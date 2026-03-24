# Test Report — {date}

## Summary

| Status | Count |
|--------|-------|
| Passed | N |
| Failed | N |
| Skipped | N |
| Errors | N |
| **Pass Rate** | **N%** |

---

## TDD Phase Assessment

{One of:}
- **RED phase**: N tests fail with ImportError — implementation not written yet. This is expected.
- **GREEN phase**: All tests pass. Ready to refactor.
- **MIXED**: N pass, N fail with real errors. Fix failures below.

---

## RED Phase Failures (expected)

These tests fail because the implementation doesn't exist yet. No action needed until you write the code.

| Test | Missing module/function |
|------|------------------------|
| `test_file.py::TestX::test_y` | `app.module.function` |

---

## Real Failures (bugs)

### `{test_file}::{test_class}::{test_name}`
- **Error**: {error type and message}
- **Probable cause**: {analysis — wrong assertion, missing mock, logic error}
- **Fix**: {specific actionable suggestion}

---

## Setup Errors

### {fixture or config issue}
- **Error**: {message}
- **Impact**: Causes N test(s) to fail
- **Fix**: {how to resolve — install dep, set env var, fix fixture}

---

## Recommendations

1. {Highest priority — fix setup errors first since they cascade}
2. {Next — fix real failures}
3. {Then — implement code to turn RED tests GREEN}
