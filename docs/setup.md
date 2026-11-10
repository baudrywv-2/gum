# GUM setup

Exact commands to run the local stack (Milestones 1–2).

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- PostgreSQL 16 (Docker Compose **or** a local install)

## 1. Clone and enter the repo

```bash
git clone https://github.com/baudrywv-2/gum.git
cd gum
```

## 2. Environment file

```bash
cp .env.example .env
```

Default values:

- `DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum`
- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- `GUM_FORCE_MOCK_PROVIDERS=true` (no paid/live provider calls)

## 3. Start PostgreSQL

### Option A — Docker Compose

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

### Option B — Local PostgreSQL

```bash
sudo pg_ctlcluster 16 main start   # Ubuntu/Debian packaging
sudo -u postgres psql -c "CREATE USER gum WITH PASSWORD 'gum' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE gum OWNER gum;"
sudo -u postgres psql -c "CREATE DATABASE gum_test OWNER gum;"
```

## 4. Python virtualenv + API dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
```

## 5. Run database migrations

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
alembic -c database/alembic.ini upgrade head
```

For the test database:

```bash
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum_test
alembic -c database/alembic.ini upgrade head
```

## 6. Start the API

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export PYTHONPATH="$(pwd):$(pwd)/services/api"
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

Expected JSON includes `"status":"ok"` and `"database":"connected"`.

Interactive docs: http://127.0.0.1:8000/docs

## 7. Start the web app

In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 — the shell page calls `/health` via the API base URL.

## 8. Run tests

```bash
source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum_test
export CHECK_DB_ON_STARTUP=false
export PYTHONPATH="$(pwd):$(pwd)/services/api"
pytest -q
```

## 9. Provider smoke (Milestone 2)

```bash
curl -s http://127.0.0.1:8000/providers
curl -s -X POST http://127.0.0.1:8000/providers/google_ads/search \
  -H 'content-type: application/json' \
  -d '{"query":"invoice automation","limit":3}'
curl -s http://127.0.0.1:8000/providers/usage
```

Details: [providers.md](providers.md).

## 10. Evidence collection smoke (Milestone 3)

```bash
curl -s -X POST http://127.0.0.1:8000/evidence/collect \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}'
curl -s 'http://127.0.0.1:8000/evidence?kind=discussion'
curl -s http://127.0.0.1:8000/evidence/pain-points
```

Details: [evidence.md](evidence.md).

## 11. Opportunity discovery smoke (Milestone 4)

```bash
curl -s -X POST http://127.0.0.1:8000/opportunities/discover \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}'
curl -s http://127.0.0.1:8000/opportunities
```

Details: [opportunity-discovery.md](opportunity-discovery.md).

## 12. Gap analysis smoke (Milestone 5)

```bash
curl -s -X POST http://127.0.0.1:8000/gaps/analyze \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}'
curl -s http://127.0.0.1:8000/gaps
```

Details: [gap-analysis.md](gap-analysis.md).

## 13. Format recommendation smoke (Milestone 6)

```bash
curl -s -X POST http://127.0.0.1:8000/formats/recommend \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}'
curl -s http://127.0.0.1:8000/formats
```

Details: [format-recommendation.md](format-recommendation.md).

## 14. Scoring & reporting smoke (Milestone 7)

```bash
curl -s -X POST http://127.0.0.1:8000/reports/generate \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}'
curl -s 'http://127.0.0.1:8000/reports?rank_by=overall_priority'
```

Details: [scoring-reporting.md](scoring-reporting.md).

## 15. Web dashboard (Milestone 8)

```bash
cd apps/web && npm run dev
# http://127.0.0.1:3000 — set NEXT_PUBLIC_API_BASE_URL if needed
```

Details: [web-dashboard.md](web-dashboard.md).

## 16. MCP smoke (Milestone 9)

```bash
export PYTHONPATH="$(pwd):$(pwd)/services/api:$(pwd)/services/mcp"
python services/mcp/server.py   # stdio for Cursor
```

Details: [mcp.md](mcp.md).

## Milestone boundaries

**M1–M9 in scope:** through Cursor MCP sharing backend engines.

**Remaining in continuous run:** validation/learning (M10). Live paid providers stay off unless credentials exist.
