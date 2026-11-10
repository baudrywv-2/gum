# Scoring and reporting (Milestone 7)

Independent, transparent score dimensions with explanations, plus structured opportunity reports that can be filtered and ranked.

## Dimensions

| Score | Meaning |
| --- | --- |
| Demand Evidence | Counts stored search/discussion/pain evidence — never invents volumes |
| Organic Ranking Feasibility | SERP observation + gap heuristics |
| Format Fit | Primary format recommender fit_score |
| Business Viability | Complexity/monetization/gap heuristics |
| Evidence Confidence | Breadth of stored provenance |
| Overall Priority | Weighted sum; **capped/zeroed when confidence is weak/absent** |

Weights live in `scoring_engine/weights.py` and are inspectable on each overall score.

## API

```bash
curl -s -X POST http://127.0.0.1:8000/reports/generate \
  -H 'content-type: application/json' \
  -d '{"query":"freelancer invoicing calculator tool","geography":"US","language":"en"}' | jq

curl -s 'http://127.0.0.1:8000/reports?rank_by=overall_priority' | jq
curl -s -X POST http://127.0.0.1:8000/reports/rank \
  -H 'content-type: application/json' \
  -d '{"rank_by":"evidence_confidence","min_evidence_confidence":0.1}' | jq
```

## Report fields

Title, summary, problem, audience, geography/language, demand evidence, keywords, discussion evidence, competitors/weaknesses, unmet needs, recommended + alternative formats, all scores, complexity, build/maintenance, monetization hypotheses, risks, source URLs, timestamps, limitations, contradictions, missing info, cheapest validation, next actions — with labeled claims.
