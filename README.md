# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 2 provider infrastructure (interfaces, mocks, config, caching, usage tracking; Google/SERP/X adapters stubbed/mocked).

## Quick start

See **[docs/setup.md](docs/setup.md)** for exact commands. Provider details: **[docs/providers.md](docs/providers.md)**.

```bash
# Postgres (Docker)
docker compose -f infrastructure/docker/docker-compose.yml up -d

# API
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/api/requirements.txt
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload

# Web (second terminal)
cd apps/web && npm install && npm run dev
```

Provider smoke:

```bash
curl -s http://127.0.0.1:8000/providers
curl -s -X POST http://127.0.0.1:8000/providers/serp/search \
  -H 'content-type: application/json' -d '{"query":"underserved niches"}'
```

## Status

Milestone 2 complete on this branch. Stop for approval before Milestone 3 (evidence collection).
