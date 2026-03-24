# Test Cases: {Feature Name} — {Phase or Context}

Generated from `{path/to/SPEC.md}`

---

## Summary

| Layer | Count | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Unit  |       |    |    |     |
| Service |     |    |    |     |
| API   |       |    |    |     |
| **Total** | **N** | **N** | **N** | **N** |

---

## Unit Tests

### UNIT-{FEATURE}-001: {Short descriptive title}
- **Priority**: P0 | P1 | P2
- **Preconditions**: {what must be true before the test runs}
- **Steps**:
  1. {action}
  2. {action}
- **Expected**: {exact observable outcome with assertion}

---

## Service Tests — {Subsection Name}

### SVC-{FEATURE}-001: {Short descriptive title}
- **Priority**: P0 | P1 | P2
- **Preconditions**: {mocks, fixtures, DB state}
- **Steps**:
  1. {action}
- **Expected**: {exact observable outcome — what was called, what was returned, what was raised}

---

## API Tests

### API-{FEATURE}-001: {METHOD} {/path} — {short title}
- **Priority**: P0 | P1 | P2
- **Preconditions**: {auth state, DB state}
- **Steps**:
  1. {HTTP request with method, path, body}
- **Expected**: {status code} with {response body shape or key fields}
