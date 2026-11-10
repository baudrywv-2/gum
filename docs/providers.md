# Provider infrastructure (Milestone 2+)

Modular, replaceable data-source adapters. **Default is MOCK** via `GUM_FORCE_MOCK_PROVIDERS=true`. Live paths exist for **X**, **SerpAPI**, and **DataForSEO** when credentials are set and force-mock is disabled.

## Package layout

```
providers/
  base.py               Provider ABC + mock_response helper
  config.py             Env credentials / force-mock flags
  cache.py              In-memory TTL cache
  usage.py              Call / cost tracking
  registry.py           Registry + search facade (SERP_PROVIDER switch)
  mock.py               Always-on mock provider
  google_ads.py         Keyword ideas (live via DataForSEO overview; native Ads stubbed)
  google_trends.py      Google Trends via SerpAPI (live when configured; else mock)
  serp.py               Google organic via SerpAPI (primary when SERP_PROVIDER=serpapi)
  dataforseo_serp.py    Google organic via DataForSEO (when SERP_PROVIDER=dataforseo)
  dataforseo_http.py    Shared DataForSEO HTTP / error helpers
  serpapi_http.py       Shared SerpAPI HTTP / error helpers
  x_api.py              X recent-search (live when configured; else mock)
packages/contracts/providers.py   Shared request/response/status models
```

## Modes

| Mode | Meaning |
| --- | --- |
| `mock` | Synthetic response; claim tag `UNVERIFIED_CLAIM`; limitations listed |
| `live` | Real provider response; claim tags distinguish observed results |
| `unavailable` | Honest hard failure (auth / quota / rate-limit / HTTP) — no fabricated volume |

`GUM_FORCE_MOCK_PROVIDERS=true` (default) keeps every adapter mocked even if credentials exist.

### X API live path

1. Set `X_API_BEARER_TOKEN` in gitignored `.env` (see `.env.example` / `apps/api/.env.example`).
2. Set `GUM_FORCE_MOCK_PROVIDERS=false`.
3. `POST /providers/x_api/search` (or `XApiProvider.search`) calls `GET {X_API_BASE_URL}/tweets/search/recent`.

Live posts are tagged `MEASURED_FACT` as **observed X posts**, with limitations that social signals are **not** purchase-intent or market-size proof. Auth (`401`/`403`), credits (`402`), and rate-limit (`429`) errors return `mode=unavailable` with empty items — never mock volume on failure.

### SerpAPI live paths (organic + Trends)

1. Set `SERPAPI_API_KEY` in gitignored `.env` (legacy `SERP_API_KEY` also accepted).
2. Optional: `SERP_API_BASE_URL=https://serpapi.com` (default).
3. Set `GUM_FORCE_MOCK_PROVIDERS=false`.
4. `POST /providers/serp/search` → `engine=google` organic results.
5. `POST /providers/google_trends/search` → `engine=google_trends` interest-over-time (same key).

Live organic hits and Trends series are tagged `MEASURED_FACT` as **observed SerpAPI payloads**, with limitations that SERP rankings / relative Trends indexes are **not** demand volume. Auth, quota, and HTTP errors return `mode=unavailable` with empty items.

### DataForSEO live paths (alternate SERP + keywords)

1. Set `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` in gitignored `.env`.
2. Set `SERP_PROVIDER=dataforseo` to route `/providers/serp` through DataForSEO (default remains `serpapi`).
3. Set `GUM_FORCE_MOCK_PROVIDERS=false`.
4. Organic: `POST /providers/serp/search` → DataForSEO `serp/google/organic/live/regular`.
5. Keywords: `POST /providers/google_ads/search` → DataForSEO Labs `keyword_overview/live` when DFS credentials are present (native Google Ads client stays stubbed).

Live rows are tagged `MEASURED_FACT` as **observed DataForSEO payloads**. Keyword `search_volume` / competition are still provider estimates — not purchase proof. Auth and balance errors return `mode=unavailable` with empty items.

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

See `.env.example`. Native Google Ads remains stubbed; keyword overview can run live via DataForSEO. **X**, **SerpAPI**, and **DataForSEO** can run live when configured and force-mock is off.

## Out of scope

Auth/workspaces, background workers, Playwright E2E, inventing demand from provider snapshots.
