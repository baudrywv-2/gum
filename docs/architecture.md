# GUM architecture

## Monorepo layout

```
apps/web                 Next.js + TypeScript UI shell
services/api             FastAPI HTTP API
providers/               Provider adapters (mocked by default)
evidence/                Evidence collection, dedupe, pain points (M3)
opportunity_engine/      Opportunity discovery (M4)
packages/contracts       Shared Pydantic contracts
database/                SQLAlchemy models + Alembic migrations
tests/                   pytest suite
infrastructure/docker/   Postgres Compose stack
docs/                    Setup and architecture notes
```

## Runtime flow

### Milestone 1 — foundation

Health API, Postgres, Alembic `health_probes`, Next.js shell.

### Milestone 2 — provider infrastructure

Provider ABC, registry, cache, usage tracking; mocked Google/SERP/X adapters.

### Milestone 3 — evidence collection

Search + discussion evidence with provenance, fingerprint dedupe, pain-point extraction.

### Milestone 4 — opportunity discovery

1. Optionally collect evidence for a query (mock providers).
2. Cluster related evidence (lexical Jaccard).
3. Detect emerging multi-provider themes.
4. Surface recurring problems from pain points.
5. Hypothesize underserved audiences (always `HYPOTHESIS`).
6. Correlate search vs discussion across sources.
7. Persist runs/clusters/opportunities; every claim labeled; no fabricated demand.

See [opportunity-discovery.md](opportunity-discovery.md).

## Deferred (post-M4)

Competitor/gap analysis (M5), format recommendation, scoring/reporting, worker/MCP, live provider clients, dashboard feature pages.

## Design rules

- Evidence before AI conclusions.
- Tag claims: MEASURED FACT | PROVIDER ESTIMATE | AI INTERPRETATION | HYPOTHESIS | UNVERIFIED CLAIM.
- Never invent demand, volumes, or market statistics.
- X/social signals are discovery signals, not purchase-intent proof.
