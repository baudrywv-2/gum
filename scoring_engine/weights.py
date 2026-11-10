"""Configurable heuristic weights for opportunity scoring.

Weights are inspectable product policy — not measured market truth.
Overall priority never compensates for zero evidence confidence.
"""

from __future__ import annotations

from packages.contracts.scoring import ScoreDimension

# Component weights for overall priority (must sum to 1.0 excluding overall itself).
DEFAULT_WEIGHTS: dict[ScoreDimension, float] = {
    ScoreDimension.DEMAND_EVIDENCE: 0.28,
    ScoreDimension.ORGANIC_RANKING_FEASIBILITY: 0.18,
    ScoreDimension.FORMAT_FIT: 0.18,
    ScoreDimension.BUSINESS_VIABILITY: 0.16,
    ScoreDimension.EVIDENCE_CONFIDENCE: 0.20,
}

# Hard gate: if evidence confidence is below this, overall is capped.
MIN_CONFIDENCE_FOR_HIGH_PRIORITY = 0.25
HIGH_PRIORITY_CAP_WITHOUT_CONFIDENCE = 0.35
