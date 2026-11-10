# GUM architecture

## Monorepo layout

```
apps/web                 Next.js + TypeScript UI shell
services/api             FastAPI HTTP API
providers/               Provider adapters (mocked by default)
evidence/                Evidence collection (M3)
opportunity_engine/      Opportunity discovery (M4)
gap_engine/              Competitor & gap analysis (M5)
format_engine/           Format recommendation (M6)
scoring_engine/          Scoring & reports (M7)
packages/contracts       Shared Pydantic contracts
database/                SQLAlchemy + Alembic
tests/                   pytest
infrastructure/docker/   Postgres Compose
docs/
```

## Milestone flow

1. **M1–M2** Foundation + mocked providers  
2. **M3** Evidence collection  
3. **M4** Opportunity discovery  
4. **M5** Competitor/gap analysis  
5. **M6** Format recommendation  
6. **M7** Scoring & reporting (transparent dimensions + structured reports)

See [scoring-reporting.md](scoring-reporting.md).

6. **M8** Web dashboard (discovery-first SaaS UI)

See [web-dashboard.md](web-dashboard.md).

## Deferred (post-M8)

MCP (M9), validation/learning (M10), live provider clients.

## Design rules

- Evidence before conclusions; labeled claims; no fabricated demand
- Prefer simple solutions when evidence supports it
- Transparent heuristics over opaque scores
