# GUM API (`services/api`)

FastAPI service for Milestone 1.

## Run

From the monorepo root:

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

## Endpoints

- `GET /health` — service + database connectivity
- `GET /docs` — OpenAPI UI
