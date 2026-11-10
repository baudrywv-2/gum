# Evidence collection (Milestone 3)

Collect and store **search** and **public discussion** evidence, extract recurring **pain points**, preserve **provenance**, and **deduplicate** by fingerprint. Uses mock/stub providers by default (`GUM_FORCE_MOCK_PROVIDERS=true`).

## Package layout

```
evidence/
  collector.py     Orchestrates provider searches → persisted evidence
  store.py         DB persistence + fingerprint dedupe
  dedupe.py        Normalization + SHA-256 fingerprints
  pain_points.py   Heuristic recurring-pain extraction
packages/contracts/evidence.py
database models: evidence_collections, evidence_records, pain_points
```

## Provenance (required on every record)

- provider + provider_mode (`mock` / `live`)
- source_url, query, geography, language
- collected_at timestamp
- claim_tag (`MEASURED_FACT` | `PROVIDER_ESTIMATE` | `AI_INTERPRETATION` | `HYPOTHESIS` | `UNVERIFIED_CLAIM`)
- reliability, limitations, raw payload reference

Mock-provider evidence is tagged `UNVERIFIED_CLAIM` with `reliability=low`.  
Extracted pain points are tagged `AI_INTERPRETATION` (never measured fact).

## Deduplication

Fingerprint = SHA-256 of `kind|provider|normalized(url|title)|normalized(summary)`.  
Identical observations are not inserted twice; the collect response reports `evidence_deduplicated`.

## API

```bash
# Collect search + discussion evidence and extract pain points
curl -s -X POST http://127.0.0.1:8000/evidence/collect \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing","geography":"US","language":"en"}' | jq

# List evidence
curl -s 'http://127.0.0.1:8000/evidence?kind=search' | jq
curl -s 'http://127.0.0.1:8000/evidence?kind=discussion' | jq

# Pain points
curl -s http://127.0.0.1:8000/evidence/pain-points | jq

# Collection summary
curl -s http://127.0.0.1:8000/evidence/collections/<collection_id> | jq
```

## Out of scope (Milestone 4+)

Opportunity discovery scoring, competitor gap analysis, format recommendation, live paid provider calls, MCP tools.
