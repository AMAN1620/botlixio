# Docker Basics — Compose, PostgreSQL, Redis

> **What is this?** Docker lets you run software (like a database) in an isolated container without installing it on your Mac. Docker Compose lets you define and start multiple containers together with one command.

---

## Key Concepts

### Container vs Image

- **Image** = a blueprint (e.g., `postgres:16-alpine` is an image)
- **Container** = a running instance of an image

Think of an image like a class definition and a container like an object instance.

### Why Docker for databases?

Instead of installing PostgreSQL and Redis directly on your Mac (messy, version conflicts), you run them in containers. When you're done, `docker compose down` removes them cleanly.

### `alpine` images

You'll see `postgres:16-alpine` and `redis:7-alpine`. Alpine is a tiny Linux distro. The alpine variant of images is smaller and faster to download.

---

## Code Examples

### Our docker-compose.yml (`docker/docker-compose.yml`)

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine        # ← which image to use
    container_name: botlixio_postgres
    environment:
      POSTGRES_USER: botlixio        # ← DB username
      POSTGRES_PASSWORD: botlixio    # ← DB password (dev only, not prod!)
      POSTGRES_DB: botlixio          # ← database name
    ports:
      - "5432:5432"    # ← host:container — connect via localhost:5432
    volumes:
      - postgres_data:/var/lib/postgresql/data   # ← persist data across restarts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U botlixio -d botlixio"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: botlixio_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

volumes:
  postgres_data:    # ← named volume so data survives container restarts
  redis_data:
```

**What this does:**
- `ports: "5432:5432"` — maps port 5432 inside the container to port 5432 on your Mac, so `localhost:5432` connects to PostgreSQL
- `volumes` — data is saved even if the container is stopped/removed
- `healthcheck` — Docker knows when the service is actually ready (not just started)

---

## Commands

```bash
# Start everything (runs in background)
docker compose -f docker/docker-compose.yml up -d

# Stop everything
docker compose -f docker/docker-compose.yml down

# Stop AND delete all data (volumes)
docker compose -f docker/docker-compose.yml down -v

# Check if containers are running
docker compose -f docker/docker-compose.yml ps

# View logs
docker compose -f docker/docker-compose.yml logs postgres
docker compose -f docker/docker-compose.yml logs -f postgres  # -f = follow (live)

# Connect to PostgreSQL directly
docker exec -it botlixio_postgres psql -U botlixio -d botlixio

# Check Redis is working
docker exec -it botlixio_redis redis-cli ping
# Should print: PONG
```

---

## The Database URL

When the FastAPI backend connects to PostgreSQL, it uses this URL format:

```
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME
                      ↑       ↑       ↑     ↑     ↑
                   botlixio botlixio localhost 5432 botlixio
```

The `+asyncpg` part tells SQLAlchemy to use the async PostgreSQL driver.

---

## Gotchas & Tips

- **Don't use `docker-compose` (with hyphen)** — old v1 syntax. Use `docker compose` (space, v2).
- **`up -d` = detached mode** — containers run in background. Without `-d` they output logs to your terminal and stop when you press Ctrl+C.
- **Data persists with named volumes** — `down` stops containers but keeps data. `down -v` deletes everything. Be careful with `-v` in production.
- **Healthchecks matter** — your backend should wait for the DB to be healthy before starting, not just started.
- **`container_name` makes commands easier** — `docker exec -it botlixio_postgres ...` works because of this name.

---

## See Also

- [environment-variables.md](environment-variables.md) — `DATABASE_URL` that uses these containers
- [python-packaging.md](python-packaging.md) — installing the `asyncpg` driver
