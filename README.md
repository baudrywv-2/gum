# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 4 opportunity discovery (recurring problems, clusters, themes, underserved audiences, cross-source correlation; mock providers; labeled claims; no fabricated demand).

## Quick start

See **[docs/setup.md](docs/setup.md)** for exact commands.

- Providers: [docs/providers.md](docs/providers.md)
- Evidence: [docs/evidence.md](docs/evidence.md)
- Discovery: [docs/opportunity-discovery.md](docs/opportunity-discovery.md)

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/api/requirements.txt
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

Discovery smoke:

```bash
curl -s -X POST http://127.0.0.1:8000/opportunities/discover \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}'
```

## Status

Milestone 4 complete on this branch. Stop for approval before Milestone 5 (competitor and gap analysis).
