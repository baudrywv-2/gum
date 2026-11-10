# GUM architecture

## Monorepo layout

```
apps/web                 Next.js + TypeScript UI shell
services/api             FastAPI HTTP API
providers/               Provider adapters (mocked by default)
evidence/                Evidence collection (M3)
opportunity_engine/      Opportunity discovery (M4)
gap_engine/              Competitor & gap analysis (M5)
packages/contracts       Shared Pydantic contracts
database/                SQLAlchemy models + Alembic migrations
tests/                   pytest suite
infrastructure/docker/   Postgres Compose stack
docs/                    Setup and architecture notes
```

## Runtime flow

### M1–M2 — foundation + providers
Health API, Postgres/Alembic, mocked provider registry/cache/usage.

### M3 — evidence collection
Search + discussion evidence with provenance, dedupe, pain points.

### M4 — opportunity discovery
Clusters, recurring problems, themes, underserved-audience hypotheses, cross-source correlation.

### M5 — competitor and gap analysis
1. Extract existing solutions from search evidence.
2. Attach discussion feedback; **weakness only with complaint-backed evidence**.
3. Flag missing feature/content gaps from pain points vs SERP coverage.
4. Compare search results vs user feedback in a gap report.
5. Persist report + competitors + findings with labeled claims.

See [gap-analysis.md](gap-analysis.md).

## Deferred (post-M5)
Format recommendation (M6), scoring/reporting, worker/MCP, live provider clients, dashboard feature pages.

## Design rules
- Evidence before AI conclusions.
- Tag claims; never invent demand or competitor weaknesses.
- Transparent `missing_info` over opaque scores.
