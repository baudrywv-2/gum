# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 6 format recommendation (primary + alternatives with evidence-backed select/reject reasons; complexity, maintenance, monetization, cheapest validation; prefer simple when evidence supports it).

## Quick start

See **[docs/setup.md](docs/setup.md)**.

- [docs/providers.md](docs/providers.md)
- [docs/evidence.md](docs/evidence.md)
- [docs/opportunity-discovery.md](docs/opportunity-discovery.md)
- [docs/gap-analysis.md](docs/gap-analysis.md)
- [docs/format-recommendation.md](docs/format-recommendation.md)

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/api/requirements.txt
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

Format smoke:

```bash
curl -s -X POST http://127.0.0.1:8000/formats/recommend \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}'
```

## Status

Milestone 6 complete on this branch. Stop for approval before Milestone 7 (scoring and reporting).
