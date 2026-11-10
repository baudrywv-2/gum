# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 3 evidence collection (search + discussion evidence, pain points, provenance, dedupe; mock providers by default).

## Quick start

See **[docs/setup.md](docs/setup.md)** for exact commands.

- Providers: **[docs/providers.md](docs/providers.md)**
- Evidence: **[docs/evidence.md](docs/evidence.md)**

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

Evidence smoke:

```bash
curl -s -X POST http://127.0.0.1:8000/evidence/collect \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}'
```

## Status

Milestone 3 complete on this branch. Stop for approval before Milestone 4 (opportunity discovery).
