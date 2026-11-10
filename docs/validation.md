# Validation & learning (Milestone 10)

Propose cheapest experiments, record measured outcomes, and decide **continue / pivot / abandon**. Projected cost/time stay separate from measured values.

## API

```bash
curl -s -X POST http://127.0.0.1:8000/validation/propose \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}' | jq

curl -s http://127.0.0.1:8000/validation/experiments | jq
curl -s -X POST http://127.0.0.1:8000/validation/experiments/<id>/outcome \
  -H 'content-type: application/json' \
  -d '{"measured_cost_usd":25,"measured_time_days":3,"results":"3 waitlist signups","decision":"continue","status":"completed"}' | jq

curl -s http://127.0.0.1:8000/validation/outcomes | jq
```

## Rules

- Hypothesis, experiment, success criteria required
- Never invent measured results
- Dashboard Validation / Outcomes pages are wired to these endpoints
