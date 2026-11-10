# GUM API (`services/api`)

FastAPI service for GUM (Milestones 1–4).

## Run

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export GUM_FORCE_MOCK_PROVIDERS=true
export PYTHONPATH="$(pwd):$(pwd)/services/api"
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

## Endpoints

- `GET /health`
- `GET /providers`, `POST /providers/{name}/search`, `GET /providers/usage`
- `POST /evidence/collect`, `GET /evidence`, `GET /evidence/pain-points`
- `POST /opportunities/discover`, `GET /opportunities`, `GET /opportunities/runs/{id}`
- `GET /docs`
