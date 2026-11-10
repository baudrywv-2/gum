# Web dashboard (Milestone 8)

Discovery-first SaaS UI in `apps/web`, wired to the FastAPI backend.

## Surfaces

| Route | Purpose |
| --- | --- |
| `/` | Overview + API health |
| `/discover` | End-to-end discover → score pipeline |
| `/intelligence/*` | SEO, X, Community, Competitors, Apps, YouTube |
| `/reports` | Ranked scored reports |
| `/reports/[id]` | Inspectable scores + labeled claims |
| `/saved` | Browser-local saved report bookmarks |
| `/validation` · `/outcomes` | Shells ready for M10 APIs |
| `/integrations` | Provider adapter status |
| `/settings` | Transparent defaults |

## Run

```bash
# API
uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000

# Web
cd apps/web && npm run dev
# open http://127.0.0.1:3000
```

Set `NEXT_PUBLIC_API_BASE_URL` if the API is not on `http://127.0.0.1:8000`.

## Quality bar

- Discovery before product recommendations
- Scores and claim tags visible in UI
- No fabricated demand volumes
- Mock providers by default
