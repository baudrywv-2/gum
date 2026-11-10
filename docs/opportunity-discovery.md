# Opportunity discovery (Milestone 4)

Discover recurring problems, cluster related evidence, surface emerging themes, hypothesize underserved audiences, and correlate signals across sources.

**Rules (quality bar):**
- Mock providers by default; no paid live calls unless explicitly configured.
- Every claim labeled: MEASURED / ESTIMATE / AI_INTERPRETATION / HYPOTHESIS / UNVERIFIED.
- Opportunities cite stored evidence IDs when available.
- Never fabricate demand, TAM, volumes, or opaque AI scores.
- Prefer transparent `missing_info` + limitations over clever but unverifiable outputs.

## Package layout

```
opportunity_engine/
  discover.py      Orchestrator (collect evidence if needed → discover)
  cluster.py       Lexical evidence clustering + cross-source correlation
  themes.py        Multi-provider emerging themes
  audiences.py     Underserved audience hypotheses
  tokens.py        Tokenization / Jaccard helpers
  store.py         Persistence
packages/contracts/opportunities.py
```

## Outputs

| Output | Claim tags | Notes |
| --- | --- | --- |
| Evidence clusters | `AI_INTERPRETATION` | Lexical similarity, not proven single problems |
| Recurring problems | `AI_INTERPRETATION` / `UNVERIFIED_CLAIM` | From pain-point frequencies in the collection |
| Emerging themes | `AI_INTERPRETATION` | Tokens spanning ≥2 providers |
| Underserved audiences | `HYPOTHESIS` | Geo/lang + discussion imbalance; size unknown |
| Cross-source correlations | `AI_INTERPRETATION` | Shared tokens across search + discussion |

Missing measured demand, TAM, and willingness-to-pay are listed under `missing_info` — never invented.

## API

```bash
curl -s -X POST http://127.0.0.1:8000/opportunities/discover \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}' | jq

curl -s 'http://127.0.0.1:8000/opportunities?run_id=<run_id>' | jq
curl -s http://127.0.0.1:8000/opportunities/runs/<run_id> | jq
```

## Out of scope (Milestone 5+)

Competitor/gap analysis, format recommendation, full scoring/reporting, live paid providers, MCP.
