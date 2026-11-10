# GUM API (`services/api`)

FastAPI service for GUM (Milestones 1–2).

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
- `GET /providers` — adapter status (all mocked in M2)
- `POST /providers/{name}/search` — mocked search (`mock`, `google_ads`, `google_trends`, `serp`, `x_api`)
- `GET /providers/usage` — usage / estimated-cost summary
- `GET /docs` — OpenAPI UI
