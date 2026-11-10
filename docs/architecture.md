# GUM architecture

## Monorepo layout

```
apps/web                 Next.js + TypeScript UI shell
services/api             FastAPI HTTP API
providers/               Provider adapters (mocked stubs by default)
evidence/                Evidence collection, dedupe, pain-point extraction (M3)
packages/contracts       Shared Pydantic contracts
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
2. Adapters: `mock`, `google_ads`, `google_trends`, `serp`, `x_api` — mocked by default.
3. API routes: `GET /providers`, `POST /providers/{name}/search`, `GET /providers/usage`.
4. Alembic adds `provider_usage_events` and `provider_cache_entries`.

See [providers.md](providers.md).

### Milestone 3 — evidence collection

1. `evidence/` collector calls providers for search + discussion signals.
2. Records persist with provenance (provider, mode, URL, query, claim tag, limitations).
3. Fingerprint dedupe prevents duplicate inserts.
4. Heuristic pain-point extraction groups recurring complaints (`AI_INTERPRETATION`).
5. API: `POST /evidence/collect`, `GET /evidence`, `GET /evidence/pain-points`, collections summary.
6. Alembic adds `evidence_collections`, `evidence_records`, `pain_points`.

See [evidence.md](evidence.md).

## Deferred directories (post-M3)

Scaffold when approved: opportunity discovery (M4), competitor gap analysis, format recommendation, scoring/reporting, `services/worker`, `services/mcp`, Redis/Celery, Playwright dashboard tests, live provider clients.

## Design rules carried from the brief

- Evidence before AI conclusions.
- Tag claims as MEASURED FACT | PROVIDER ESTIMATE | AI INTERPRETATION | HYPOTHESIS | UNVERIFIED CLAIM.
- Solution-format agnostic recommendations (not always websites).
- Transparent scoring dimensions (implemented later).
- X/social signals are discovery signals, not market-size proof.
