# FastAPI Basics

> **What is this?** FastAPI is a modern Python web framework for building REST APIs. It's fast, uses Python type hints for automatic validation, and generates interactive API docs automatically.

---

## Key Concepts

### The App Factory Pattern

Instead of creating the FastAPI `app` directly at the module level, we wrap it in a `create_app()` function. This is called the **factory pattern** — it lets you create multiple instances of the app (e.g., for testing) with different configs.

```
create_app() → configures middleware + routes → returns app
```

### CORS (Cross-Origin Resource Sharing)

Browsers block requests from one domain (e.g., `localhost:3000`) to another (e.g., `localhost:8000`) by default. CORS middleware tells the browser "it's OK, I trust those origins."

---

## Code Examples

### Our app factory (`backend/app/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title="Botlixio API",
        docs_url="/api/docs",       # ← Swagger UI at this URL
        redoc_url="/api/redoc",     # ← ReDoc alternative docs
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # ← our Next.js frontend
        allow_credentials=True,
        allow_methods=["*"],    # ← allow GET, POST, PUT, DELETE, etc.
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

app = create_app()   # ← uvicorn looks for this
```

**What this does line by line:**
- `FastAPI(...)` creates the app with metadata used in the auto-generated docs
- `add_middleware(CORSMiddleware, ...)` allows the frontend to call this API
- `@app.get("/health")` registers a GET endpoint at `/health`
- `async def health()` — FastAPI supports `async` functions natively
- The last line `app = create_app()` is what `uvicorn app.main:app` finds

### Starting the dev server

```bash
uvicorn app.main:app --reload
# --reload → auto-restarts when you change a file (dev only!)
```

Then visit:
- `http://localhost:8000/health` → `{"status": "ok"}`
- `http://localhost:8000/api/docs` → Interactive Swagger UI (free, auto-generated!)

---

## Commands

```bash
# Start the development server
cd backend/
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Start on a specific host (needed if running in Docker)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## How Routes Work (Preview)

FastAPI uses **decorators** to register routes:

```python
@app.get("/users")          # HTTP method + path
async def get_users():
    return [{"id": 1}]      # FastAPI auto-converts dict → JSON

@app.post("/users")
async def create_user(data: UserCreate):   # Pydantic model = auto-validation
    ...
```

Routes will be split into separate router files as we build each feature (see `app/api/v1/`).

---

## Gotchas & Tips

- **`app = create_app()` must be at module level** — uvicorn needs to import `app` from `app.main`. If it's inside a function, uvicorn can't find it.
- **`async def` vs `def`** — Use `async def` for all route handlers in FastAPI. Regular `def` works but won't benefit from async performance.
- **Auto docs are free** — FastAPI generates Swagger UI at `/api/docs` with no extra work. Use it constantly for testing.
- **CORS must come before routers** — middleware order matters; add CORS middleware before registering any routers.

---

## See Also

- [python-packaging.md](python-packaging.md) — how the project is set up to run FastAPI
- [testing-fastapi.md](testing-fastapi.md) — how to test FastAPI endpoints
- `docs/features/` — feature-by-feature API design
