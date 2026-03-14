# Alembic Migrations — Database Versioning

> **What is this?** Alembic tracks changes to your SQLAlchemy models and generates SQL scripts to update the database. It's like Git but for your database schema — each migration is a versioned step that can be applied or reverted.

---

## Key Concepts

### Why not just `CREATE TABLE` manually?

When you change a model (add a field, rename a column), you need to update the database to match. You could write SQL by hand, but:
- Easy to forget a change
- Hard to apply the same change on multiple environments (dev, staging, prod)
- No way to undo a mistake

Alembic **autogenerates** the SQL by comparing your Python models to the current database.

### The Migration Workflow

```
1. You change a model in Python (e.g., add a field)
2. Run: alembic revision --autogenerate -m "add phone to user"
3. Alembic creates a migration script in alembic/versions/
4. Run: alembic upgrade head
5. Database is updated to match your models
```

### `head` = latest version

Think of migrations like a linked list:

```
initial → add_users → add_agents → add_subscriptions
                                        ↑
                                       head
```

`alembic upgrade head` applies all unapplied migrations to reach the latest version.

---

## Code Examples

### Alembic setup in this project

```
backend/
├── alembic.ini                 ← Main config (DB URL, logging)
├── alembic/
│   ├── env.py                  ← Connects Alembic to our models
│   ├── script.py.mako          ← Template for new migrations
│   └── versions/               ← Generated migration scripts go here
│       └── 001_initial_schema.py  ← (will be generated)
```

### The env.py trick — async support

Regular Alembic uses synchronous database connections. We use async SQLAlchemy, so our `env.py` needs special handling:

```python
# alembic/env.py (key parts)

from app.core.database import Base           # ← our DeclarativeBase
from app.models import *                      # ← import ALL models (so metadata knows tables)

target_metadata = Base.metadata               # ← Alembic reads table definitions from here

async def run_async_migrations():
    connectable = create_async_engine(config.get_main_option("sqlalchemy.url"))
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

**Critical:** `from app.models import *` — without this line, `Base.metadata` is empty and Alembic won't see any tables. This is why we have `app/models/__init__.py` importing everything.

### What a migration looks like

```python
# alembic/versions/xxx_initial_schema.py (auto-generated)

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('full_name', sa.String(255)),
        ...
    )
    op.create_table(
        'agents',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('user_id', UUID(), sa.ForeignKey('users.id')),
        ...
    )

def downgrade():
    op.drop_table('agents')     # ← reverse order (agents first, because of FK)
    op.drop_table('users')
```

**`upgrade()`** = apply the change. **`downgrade()`** = undo it. Alembic generates both.

---

## Commands

```bash
# Initial setup (already done in Phase 0)
alembic init alembic

# Generate a migration by comparing models to current DB
alembic revision --autogenerate -m "initial_schema"

# Apply all pending migrations
alembic upgrade head

# See current migration version
alembic current

# See migration history
alembic history

# Undo the last migration
alembic downgrade -1

# Undo ALL migrations (back to empty DB)
alembic downgrade base

# Generate migration without actually creating tables (dry run)
alembic revision --autogenerate -m "description" --sql
```

---

## Gotchas & Tips

- **Start PostgreSQL first** — `alembic upgrade head` connects to the database. If it's not running, you get a connection error. Run `docker compose up -d` first.
- **Import ALL models in `__init__.py`** — if a model isn't imported, Alembic doesn't know about it. Our `app/models/__init__.py` imports every model for exactly this reason.
- **Always review auto-generated migrations** — autogenerate is good but not perfect. It might miss:
  - Renamed columns (shows as drop + add instead of rename)
  - Data migrations (it only handles schema changes)
  - Some index or constraint changes
- **`alembic/versions/` empty = no tables** — if you haven't generated a migration, `alembic upgrade head` does nothing. The database stays empty.
- **Don't edit migration files after sharing them** — once a migration has been applied in staging/prod, treat it as immutable. Create a new migration instead.
- **Downgrade before deleting a migration** — if you need to redo a migration: `alembic downgrade -1`, delete the file, regenerate.

---

## See Also

- [sqlalchemy-async.md](sqlalchemy-async.md) — the models that Alembic reads
- [docker-basics.md](docker-basics.md) — the PostgreSQL container Alembic connects to
- [pydantic-settings.md](pydantic-settings.md) — where `DATABASE_URL` comes from
- `docs/database-schema.md` — the full schema these migrations should produce
