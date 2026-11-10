# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Current:** Milestone 7 scoring & reporting (independent transparent scores + structured opportunity reports + filter/rank).

## Quick start

See **[docs/setup.md](docs/setup.md)**.

Docs: providers · evidence · opportunity-discovery · gap-analysis · format-recommendation · [scoring-reporting](docs/scoring-reporting.md)

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/api/requirements.txt
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
alembic -c database/alembic.ini upgrade head
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

```bash
curl -s -X POST http://127.0.0.1:8000/reports/generate \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}'
```

## Status

Milestone 7 complete on this branch (continuous M7–M10 run after blanket approval).
