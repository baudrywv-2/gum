# GUM — Opportunity Intelligence Engine

Discover real problems and unmet demand, collect evidence, then recommend what to build.

**Milestone 1 (this branch):** monorepo foundation only — Next.js web shell, FastAPI health API, PostgreSQL + Alembic, shared contracts, mock provider stub, tests, and setup docs.

## Quick start

See **[docs/setup.md](docs/setup.md)** for exact commands.

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

## Status

Milestone 1 foundation. Stop for approval before Milestone 2 (provider infrastructure).
