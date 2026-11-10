# GUM MCP server (`services/mcp`)

Cursor MCP interface over the **same engines** as the HTTP API — no duplicated intelligence logic.

## Tools

| Tool | Engine |
| --- | --- |
| `discover_opportunities` | opportunity_engine |
| `research_niche` | evidence + opportunity_engine |
| `find_seo_gaps` | gap_engine (content gaps) |
| `search_x_conversations` | providers X adapter |
| `extract_user_pain_points` | evidence |
| `analyse_competitors` | gap_engine |
| `compare_solution_formats` | format_engine |
| `score_opportunity` | scoring_engine |
| `validate_opportunity_across_sources` | opportunity_engine correlations |
| `generate_opportunity_report` | scoring_engine reports |
| `save_opportunity` | saved_opportunities |
| `get_opportunity_details` | scoring_engine store |

## Run (stdio)

```bash
cd /path/to/gum
source .venv/bin/activate
pip install -r services/api/requirements.txt -r services/mcp/requirements.txt
export DATABASE_URL=postgresql+psycopg2://gum:gum@localhost:5432/gum
export GUM_FORCE_MOCK_PROVIDERS=true
export PYTHONPATH="$(pwd):$(pwd)/services/api:$(pwd)/services/mcp"
python services/mcp/server.py
```

## Cursor MCP config sketch

```json
{
  "mcpServers": {
    "gum": {
      "command": "python",
      "args": ["services/mcp/server.py"],
      "cwd": "/absolute/path/to/gum",
      "env": {
        "DATABASE_URL": "postgresql+psycopg2://gum:gum@localhost:5432/gum",
        "GUM_FORCE_MOCK_PROVIDERS": "true",
        "PYTHONPATH": "/absolute/path/to/gum:/absolute/path/to/gum/services/api:/absolute/path/to/gum/services/mcp"
      }
    }
  }
}
```
