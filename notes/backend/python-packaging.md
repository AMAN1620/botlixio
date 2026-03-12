# Python Packaging with pyproject.toml

> **What is this?** The modern way to define a Python project — its name, dependencies, and tool configuration — all in one file called `pyproject.toml`.

---

## Key Concepts

In older Python projects, you'd have `setup.py`, `requirements.txt`, `setup.cfg`, and `tox.ini` all separately. `pyproject.toml` replaces all of them.

Think of it like `package.json` in Node.js — one file that describes everything about your project.

### The three sections you need to know

```
[build-system]   → tells pip HOW to build/install your package
[project]        → metadata: name, version, dependencies
[tool.pytest]    → configuration for tools like pytest, ruff
```

---

## Code Examples

### Our pyproject.toml (simplified)

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"   # ← use this, not "setuptools.backends.legacy:build"

[project]
name = "botlixio"
version = "2.0.0"
requires-python = ">=3.12"               # ← minimum Python version
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    # ... more deps
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"     # ← makes all async tests work automatically
testpaths = ["tests"]     # ← only look in the tests/ folder
addopts = "-v --tb=short" # ← verbose output, short tracebacks
```

**What this does:**
- `dependencies` = always installed (production)
- `[dev]` = only installed when you do `pip install -e ".[dev]"`
- `asyncio_mode = "auto"` = no need to decorate each async test with `@pytest.mark.asyncio`

---

## Commands

```bash
# Create a virtual environment (always use Python 3.12 for this project)
/opt/homebrew/bin/python3.12 -m venv .venv

# Activate the venv (do this every time you open a terminal)
source .venv/bin/activate

# Install project + dev dependencies in editable mode
pip install -e ".[dev]"

# Upgrade pip first if you see warnings
pip install --upgrade pip

# Check which Python is being used (should show .venv path)
which python
```

---

## Gotchas & Tips

- **`build-backend = "setuptools.backends.legacy:build"` doesn't work for editable installs.** Use `"setuptools.build_meta"` instead. This broke our first install attempt.
- **System Python on macOS is 3.9** — too old. Always use `/opt/homebrew/bin/python3.12` to create the venv.
- **`pip install -e ".[dev]"` with editable mode** — the `-e` flag means changes to your source code take effect immediately without reinstalling. Great for development.
- **Activate the venv every time** — if you see `command not found: pytest` it's because you forgot to activate `.venv`.

---

## See Also

- [testing-fastapi.md](testing-fastapi.md) — pytest setup that uses this pyproject.toml config
- [environment-variables.md](environment-variables.md) — the `.env` file that works alongside this
