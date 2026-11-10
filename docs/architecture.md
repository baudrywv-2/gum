# GUM architecture (Milestone 1)

## Monorepo layout

```
apps/web                 Next.js + TypeScript UI shell
services/api             FastAPI HTTP API
packages/contracts       Shared Pydantic contracts (claim tags, health, providers)
database/                SQLAlchemy models + Alembic migrations
tests/                   pytest suite
infrastructure/docker/   Postgres Compose stack
docs/                    Setup and architecture notes
```

## Runtime flow (M1)

1. `apps/web` loads a foundation shell and optionally fetches `GET /health`.
2. `services/api` exposes `/health`, checks Postgres, returns status JSON.
3. Alembic owns schema via `database/alembic` (initial `health_probes` table).
4. `packages/contracts` defines claim tags and mock provider result shapes for later milestones.
5. `MockProvider` is the only provider implementation; no paid APIs.

## Deferred directories (post-M1)

Scaffold placeholders only when approved: `services/worker`, `services/mcp`, engine packages, real `providers/*`, Redis/Celery, Playwright dashboard tests.

## Design rules carried from the brief

- Evidence before AI conclusions.
- Tag claims as MEASURED FACT | PROVIDER ESTIMATE | AI INTERPRETATION | HYPOTHESIS | UNVERIFIED CLAIM.
- Solution-format agnostic recommendations (not always websites).
- Transparent scoring dimensions (implemented later).
