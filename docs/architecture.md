# GUM architecture

## Monorepo layout

```
apps/web                 Next.js + TypeScript UI shell
services/api             FastAPI HTTP API
providers/               Provider adapters (M2 — mocked stubs)
packages/contracts       Shared Pydantic contracts (claim tags, health, providers)
database/                SQLAlchemy models + Alembic migrations
tests/                   pytest suite
infrastructure/docker/   Postgres Compose stack
docs/                    Setup and architecture notes
```

## Runtime flow

### Milestone 1 — foundation

1. `apps/web` loads a foundation shell and optionally fetches `GET /health`.
2. `services/api` exposes `/health`, checks Postgres, returns status JSON.
3. Alembic owns schema via `database/alembic` (`health_probes`).

### Milestone 2 — provider infrastructure

1. Top-level `providers/` package defines a `Provider` ABC, registry, TTL cache, and usage tracker.
2. Adapters: `mock`, `google_ads`, `google_trends`, `serp`, `x_api` — **all explicitly MOCK** in M2.
3. API routes: `GET /providers`, `POST /providers/{name}/search`, `GET /providers/usage`.
4. Alembic adds `provider_usage_events` and `provider_cache_entries`.
5. No paid API calls; credentials are optional placeholders only.

See [providers.md](providers.md).

## Deferred directories (post-M2)

Scaffold when approved: evidence collection (M3), discovery engines, `services/worker`, `services/mcp`, Redis/Celery, Playwright dashboard tests, live provider clients.

## Design rules carried from the brief

- Evidence before AI conclusions.
- Tag claims as MEASURED FACT | PROVIDER ESTIMATE | AI INTERPRETATION | HYPOTHESIS | UNVERIFIED CLAIM.
- Solution-format agnostic recommendations (not always websites).
- Transparent scoring dimensions (implemented later).
- X/social signals are discovery signals, not market-size proof.
