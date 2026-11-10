# Competitor and gap analysis (Milestone 5)

Identify existing solutions, compare search results with user feedback, and produce **evidence-backed** gap reports.

**Hard rule:** never label a competitor weak without discussion evidence that contains complaint cues and cites evidence IDs.

## Quality bar

- Coherent, production-minded engine + API
- Skilled-user UX: clear statuses, labeled claims, explicit `missing_info`
- Claim tags on every assertion
- No fabricated demand, market share, or invented weaknesses

## Package layout

```
gap_engine/
  analyze.py       Orchestrator (collect evidence if needed → analyze)
  competitors.py   Extract existing solutions from search evidence
  gaps.py          Feedback attach, missing-feature gaps, weakness gate
  store.py         Persistence
packages/contracts/gaps.py
```

## Competitor statuses

| Status | Meaning |
| --- | --- |
| `observed_in_search` | Seen in SERP/search evidence only |
| `mentioned_in_feedback` | Named in discussion without complaint cues |
| `no_weakness_evidence` | Explicitly: not enough evidence to call weak |
| `weakness_evidenced` | Discussion evidence + complaint cues + evidence IDs |

## API

```bash
curl -s -X POST http://127.0.0.1:8000/gaps/analyze \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}' | jq

curl -s http://127.0.0.1:8000/gaps | jq
curl -s http://127.0.0.1:8000/gaps/<report_id> | jq
```

## Out of scope (Milestone 6+)

Format recommendation, full scoring/reporting, live paid provider clients, MCP, dashboard pages.
