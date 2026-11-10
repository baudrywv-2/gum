# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 8 web dashboard (discovery-first SaaS UI wired to the API).

## Quick start

See **[docs/setup.md](docs/setup.md)** and **[docs/web-dashboard.md](docs/web-dashboard.md)**.

```bash
# API
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload

# Web
cd apps/web && npm run dev
```

## Status

Continuous M7–M10 run after blanket approval. Milestone 8 on this branch.
