# Provider infrastructure (Milestone 2)

Modular, replaceable data-source adapters. **All adapters run in explicit MOCK mode in M2** — no paid or live API calls are issued.

## Package layout

```
providers/
  base.py            Provider ABC + mock_response helper
  config.py          Env credentials / force-mock flags
  cache.py           In-memory TTL cache
  usage.py           Call / cost tracking
  registry.py        Registry + search facade
  mock.py            Always-on mock provider
  google_ads.py      Keyword Planner stub (mocked)
  google_trends.py   Trends stub (mocked)
  serp.py            SERP stub (mocked)
  x_api.py           X recent-search stub (mocked)
packages/contracts/providers.py   Shared request/response/status models
```

## Modes

| Mode | Meaning |
| --- | --- |
| `mock` | Synthetic response; claim tag `UNVERIFIED_CLAIM`; limitations listed |
| `live` | Reserved for future real clients (not used in M2) |
| `unavailable` | Reserved for hard failures |

`GUM_FORCE_MOCK_PROVIDERS=true` (default) keeps every adapter mocked even if credentials exist.

## API

```bash
# List adapters + cache stats
curl -s http://127.0.0.1:8000/providers | jq

# Mock search (Google Ads stub)
curl -s -X POST http://127.0.0.1:8000/providers/google_ads/search \
  -H 'content-type: application/json' \
  -d '{"query":"invoice automation","limit":5}' | jq

# Usage / estimated cost summary
curl -s http://127.0.0.1:8000/providers/usage | jq
```

## Database

Migration `20261110_0002` adds:

- `provider_usage_events` — durable usage accounting rows
- `provider_cache_entries` — optional durable cache payloads (in-memory cache is primary in M2)

## Credential placeholders

See `.env.example`. Setting keys does **not** enable live calls in Milestone 2; adapters remain stubs until a later milestone implements real clients.

## Out of scope (Milestone 3+)

Evidence collection pipelines, discovery engines, scoring, MCP tools.
