# Testing FastAPI with pytest

> **What is this?** pytest is Python's most popular testing framework. pytest-asyncio extends it to handle `async` test functions — which we need because FastAPI is async.

---

## Key Concepts

### Why TDD (Test-Driven Development)?

This project follows TDD: **write the test first, then write the code to make it pass**.

```
Red  → Write a failing test (describes what you want)
Green → Write minimum code to make it pass
Refactor → Clean up while keeping tests green
```

This catches bugs before they happen and documents how code is supposed to work.

### Test Layers in this Project

| Layer | Where | Tests what |
|-------|-------|-----------|
| Unit | `tests/unit/` | Pure functions (no database, no HTTP) |
| Integration | `tests/integration/` | Full API endpoints (HTTP requests) |

---

## Code Examples

### Basic conftest.py (`backend/tests/conftest.py`)

```python
import pytest

@pytest.fixture
def anyio_backend() -> str:
    """Tell pytest-asyncio to use asyncio (not trio)."""
    return "asyncio"
```

**What this does:** `conftest.py` is a special file pytest loads automatically. Fixtures defined here are available to ALL test files without importing.

### A simple unit test (example)

```python
# tests/unit/test_something.py

def test_addition():
    assert 1 + 1 == 2

async def test_async_thing():
    result = await some_async_function()
    assert result == "expected"
```

Because we set `asyncio_mode = "auto"` in `pyproject.toml`, async tests work without any extra decorator.

### Running tests

```bash
# Run all tests
python -m pytest

# Run only unit tests
python -m pytest tests/unit/

# Show detailed output, stop on first failure
python -m pytest -v -x

# Collect tests only (don't run them) — useful to verify setup
python -m pytest --co -q
```

---

## Commands

```bash
# Verify pytest is working (should say "0 tests collected" in Phase 0)
cd backend/
source .venv/bin/activate
python -m pytest --co -q

# Run tests with coverage report
python -m pytest --cov=app tests/
```

---

## Gotchas & Tips

- **Exit code 5 = no tests collected** — this is NOT an error! It means pytest ran successfully but found 0 tests. In Phase 0 this is correct.
- **Exit code 1 = test failure** — this is the "red" phase in TDD. Expected when you write a test before implementing the code.
- **`asyncio_mode = "auto"` in pyproject.toml** — without this, every async test needs `@pytest.mark.asyncio`. Setting it globally saves typing.
- **`conftest.py` is auto-loaded** — don't import from it. Fixtures defined there are available everywhere automatically.
- **`python -m pytest` vs `pytest`** — use `python -m pytest` to ensure you're using the venv's pytest, not a global one.

---

## See Also

- [python-packaging.md](python-packaging.md) — pyproject.toml where `asyncio_mode = "auto"` is set
- [fastapi-basics.md](fastapi-basics.md) — what we're testing
- `docs/tech-stack.md` — full testing strategy with examples
