# Provider infrastructure (Milestone 2)

Modular, replaceable data-source adapters. **Default is MOCK** via `GUM_FORCE_MOCK_PROVIDERS=true`. The X adapter can run **live recent-search** when a bearer token is set and force-mock is disabled.

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
  x_api.py           X recent-search (live when configured; else mock)
packages/contracts/providers.py   Shared request/response/status models
```

## Modes

| Mode | Meaning |
| --- | --- |
| `mock` | Synthetic response; claim tag `UNVERIFIED_CLAIM`; limitations listed |
| `live` | Real provider response (X recent-search only today); claim tags distinguish observed posts |
| `unavailable` | Honest hard failure (auth / rate-limit / HTTP) — no fabricated volume |

`GUM_FORCE_MOCK_PROVIDERS=true` (default) keeps every adapter mocked even if credentials exist.

### X API live path

1. Set `X_API_BEARER_TOKEN` in gitignored `.env` (see `.env.example` / `apps/api/.env.example`).
2. Set `GUM_FORCE_MOCK_PROVIDERS=false`.
3. `POST /providers/x_api/search` (or `XApiProvider.search`) calls `GET {X_API_BASE_URL}/tweets/search/recent`.

Live posts are tagged `MEASURED_FACT` as **observed X posts**, with limitations that social signals are **not** purchase-intent or market-size proof. Auth (`401`/`403`) and rate-limit (`429`) errors return `mode=unavailable` with empty items — never mock volume on failure.

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

See `.env.example`. Most adapters remain stubs. **X** is the exception: with `X_API_BEARER_TOKEN` and `GUM_FORCE_MOCK_PROVIDERS=false`, recent-search runs live (read-only).

## Out of scope (Milestone 3+)

Evidence collection pipelines, discovery engines, scoring, MCP tools.
