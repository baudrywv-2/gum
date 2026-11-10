# GUM API (`services/api`)

FastAPI service for GUM (Milestones 1–5).

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
- Providers: `GET /providers`, `POST /providers/{name}/search`, `GET /providers/usage`
- Evidence: `POST /evidence/collect`, `GET /evidence`, `GET /evidence/pain-points`
- Opportunities: `POST /opportunities/discover`, `GET /opportunities`
- Gaps: `POST /gaps/analyze`, `GET /gaps`, `GET /gaps/{id}`
- `GET /docs`
