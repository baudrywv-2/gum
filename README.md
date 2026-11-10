# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 5 competitor & gap analysis (existing solutions, missing features/content, search vs feedback, evidence-backed gaps; never label competitors weak without evidence).

## Quick start

See **[docs/setup.md](docs/setup.md)**.

- Providers: [docs/providers.md](docs/providers.md)
- Evidence: [docs/evidence.md](docs/evidence.md)
- Discovery: [docs/opportunity-discovery.md](docs/opportunity-discovery.md)
- Gaps: [docs/gap-analysis.md](docs/gap-analysis.md)

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/api/requirements.txt
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

Gap analysis smoke:

```bash
curl -s -X POST http://127.0.0.1:8000/gaps/analyze \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}'
```

## Status

Milestone 5 complete on this branch. Stop for approval before Milestone 6 (format recommendation).
