# Format recommendation (Milestone 6)

Compare solution formats and recommend a **primary** format plus **alternatives** / **complementary** options with evidence-backed select/reject reasons.

Formats evaluated: SEO website/blog, Android/iOS apps, web app, YouTube, calculator/tool, directory, marketplace, newsletter/alerts, SaaS, API/data service, AI agent, digital product, professional services.

## Quality bar

- Recommendations are **hypotheses**, not prescriptions
- Every reason is claim-tagged and tied to stored evidence when available
- Transparent `fit_score` heuristic — **not** fabricated demand
- Complexity, maintenance, monetization hypotheses, cheapest validation on every evaluation
- Prefer simpler formats when evidence support is similar
- Do **not** auto-recommend a website

## API

```bash
curl -s -X POST http://127.0.0.1:8000/formats/recommend \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}' | jq

curl -s http://127.0.0.1:8000/formats | jq
curl -s http://127.0.0.1:8000/formats/<recommendation_id> | jq
```

## Package layout

```
format_engine/
  catalog.py      Format baselines (complexity/maintenance/validation)
  signals.py      Evidence → format signals
  recommend.py    Scoring + select/reject + anti-default-website
  store.py        Persistence
```

## Out of scope (Milestone 7+)

Full scoring/reporting dashboards, live paid providers, MCP, rich web UI pages.
