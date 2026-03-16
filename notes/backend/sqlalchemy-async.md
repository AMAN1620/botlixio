# SQLAlchemy Async — Database Models & Sessions

> **What is this?** SQLAlchemy is Python's most popular ORM (Object-Relational Mapper). It lets you work with database tables as Python classes. The "async" part means it works with `async/await` — essential for FastAPI which is async by nature.

---

## Key Concepts

### ORM = Tables as Classes

Instead of writing raw SQL, you define a Python class that "maps" to a database table:

```
SQL table:  users (id, email, name)
     ↕
Python class: User(id, email, name)
```

### SQLAlchemy 2.0 Style

SQLAlchemy 2.0 introduced a cleaner syntax using `Mapped[]` type annotations. This project uses this modern style:

```python
# Old style (SQLAlchemy 1.x) — don't use this
email = Column(String(255), unique=True)

# New style (SQLAlchemy 2.0) — what we use
email: Mapped[str] = mapped_column(String(255), unique=True)
```

### DeclarativeBase

All models inherit from `Base`, which is our `DeclarativeBase`. This base class holds a `metadata` object that knows about ALL tables — Alembic uses this to autogenerate migrations.

### AsyncSession

A **session** is a workspace that tracks changes to objects. When you modify a model instance, the session remembers the change. When you call `commit()`, it sends the SQL to the database.

```
Create session → Load/modify objects → commit() → changes saved to DB
                                     → rollback() → changes discarded
```

---

## Code Examples

### Database setup (`backend/app/core/database.py`)

```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# 1. DeclarativeBase — all models inherit from this
class Base(DeclarativeBase):
    pass

# 2. Engine — the actual database connection
engine = create_async_engine(
    settings.DATABASE_URL,     # postgresql+asyncpg://...
    echo=settings.DEBUG,       # True = print SQL to console (dev only)
    pool_pre_ping=True,        # Check connection is alive before using it
)

# 3. Session factory — creates sessions on demand
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Don't expire objects after commit
)

# 4. FastAPI dependency — one session per request
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**What this does:**
- `create_async_engine(...)` — opens a pool of connections to PostgreSQL
- `async_sessionmaker(...)` — a factory that creates `AsyncSession` instances
- `get_db()` — a FastAPI **dependency** (injected into route handlers). It creates a session, gives it to the handler, then commits or rolls back.

### Defining a model (`backend/app/models/user.py`)

```python
import uuid
from datetime import datetime
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"    # ← actual SQL table name

    # Primary key — UUID, auto-generated
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Regular columns
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    # Nullable column  (str | None)
    password_hash: Mapped[str | None] = mapped_column(String(255))

    # Server-side default (PostgreSQL generates the timestamp)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships (links to other models)
    agents: Mapped[list["Agent"]] = relationship(back_populates="user")
```

**Key patterns:**
- `Mapped[str]` = required, not nullable
- `Mapped[str | None]` = nullable
- `default=True` = Python-side default (set when you create the object)
- `server_default=func.now()` = PostgreSQL-side default (set when the row is inserted)
- `UUID(as_uuid=True)` = stores as PostgreSQL's native UUID type
- `relationship(back_populates="user")` = bidirectional ORM relationship

### Enums (`backend/app/models/enums.py`)

```python
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
```

**Why `(str, enum.Enum)`?** The `str` mixin makes the enum serialize to `"admin"` in JSON responses automatically. Without it, FastAPI would serialize it as `UserRole.ADMIN`.

---

## Using sessions in route handlers

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

`Depends(get_db)` tells FastAPI: "create a database session, give it to me as `db`, and close it when I'm done."

---

## Commands

```bash
# Test database module
cd backend/
python -m pytest tests/unit/test_database.py -v

# Check models are importable
python -c "from app.models import User, Agent; print('Models loaded OK')"
```

---

## Gotchas & Tips

- **`expire_on_commit=False`** — without this, accessing `user.email` after a commit raises an error because SQLAlchemy "expires" (forgets) the object. Setting this to False keeps data accessible after commit.
- **`pool_pre_ping=True`** — PostgreSQL drops idle connections after a while. Pre-ping detects dead connections and reconnects. Without it, you'd get random connection errors.
- **`Mapped[list["Agent"]]` uses string quotes** — the quotes around `"Agent"` are needed because `Agent` is defined in another file. Python resolves the string later (forward reference).
- **`server_default` vs `default`** — `default` is set by Python when you create an object. `server_default` is set by PostgreSQL when you INSERT. For timestamps, prefer `server_default=func.now()` so the DB's clock is used (consistent even with multiple app servers).
- **Don't forget `__tablename__`** — without it, SQLAlchemy guesses the table name from the class name. Explicit is better.
- **`TIMESTAMP WITHOUT TIME ZONE` and Datetimes** — PostgreSQL's timezone naive columns do NOT accept timezone-aware python datetimes. If you use `datetime.now(timezone.utc)`, asyncpg will throw `DataError: can't subtract offset-naive and offset-aware datetimes`. Fix: use `datetime.utcnow()` (or equivalent Python 3.11+ naive UTC functions) when writing to naive columns.
- **ASGI, Dependency Injection, and ORM Caching** — When writing API tests with `httpx.AsyncClient` that override the `get_db` session, SQLAlchemy's `setattr` + `flush()` change-tracking might fail to propagate `UPDATE` statements between successive test requests sharing the same async event scope. For critical state changes (like invalidating a token), an explicit SQL `UPDATE` instead of `setattr()` avoids identity-map caching bugs.

---

## See Also

- [pydantic-settings.md](pydantic-settings.md) — provides `DATABASE_URL` used here
- [alembic-migrations.md](alembic-migrations.md) — creates tables from these models
- [docker-basics.md](docker-basics.md) — runs the PostgreSQL database these models connect to
- `docs/database-schema.md` — the complete schema documentation
