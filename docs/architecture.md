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
packages/contracts       Shared Pydantic contracts
database/                SQLAlchemy + Alembic
tests/                   pytest
infrastructure/docker/   Postgres Compose
docs/
```

## Milestone flow

1. **M1–M2** Foundation + mocked providers  
2. **M3** Evidence collection (search/discussion/pain points/provenance/dedupe)  
3. **M4** Opportunity discovery (clusters/themes/audiences/correlation)  
4. **M5** Competitor/gap analysis (no weak labels without evidence)  
5. **M6** Format recommendation (primary/alternatives/complementary/rejected with reasons)

See [format-recommendation.md](format-recommendation.md).

## Deferred (post-M6)

Scoring/reporting (M7), web dashboard (M8), MCP (M9), validation/learning (M10), live provider clients.

## Design rules

- Evidence before conclusions; labeled claims; no fabricated demand
- Prefer simple solutions when evidence supports it
- Transparent heuristics over opaque scores
