# GUM API (`services/api`)

FastAPI service for GUM (Milestones 1–3).

## Run

From the monorepo root:

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export GUM_FORCE_MOCK_PROVIDERS=true
export PYTHONPATH="$(pwd):$(pwd)/services/api"
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

## Endpoints

- `GET /health` — service + database connectivity
- `GET /providers` — adapter status (mocked by default)
- `POST /providers/{name}/search` — provider search
- `GET /providers/usage` — usage / estimated-cost summary
- `POST /evidence/collect` — collect search + discussion evidence, extract pain points
- `GET /evidence` — list evidence (`kind`, `collection_id` filters)
- `GET /evidence/pain-points` — recurring pain points
- `GET /evidence/collections/{id}` — collection summary
- `GET /docs` — OpenAPI UI
