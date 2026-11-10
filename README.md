# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 9 Cursor MCP (shared engines; stdio tools).

## Quick start

See **[docs/setup.md](docs/setup.md)**, **[docs/web-dashboard.md](docs/web-dashboard.md)**, **[docs/mcp.md](docs/mcp.md)**.

```bash
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api:$(pwd)/services/mcp"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
# MCP: python services/mcp/server.py
```

## Status

Continuous M7–M10 run. Milestone 9 on this branch; M10 next.
