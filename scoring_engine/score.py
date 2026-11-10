"""Transparent multi-dimension scoring over stored evidence.

Never invent demand volumes. Never let AI scores compensate for no evidence.
"""

from __future__ import annotations

from uuid import UUID

from format_engine.catalog import FORMAT_CATALOG
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceKind, EvidenceRecord, PainPoint
from packages.contracts.formats import FormatRecommendation, SolutionFormat
from packages.contracts.gaps import CompetitorStatus, GapReport
from packages.contracts.opportunities import LabeledClaim, Opportunity
from packages.contracts.scoring import OpportunityScores, ScoreDimension, ScoreExplanation
from scoring_engine.weights import (
    DEFAULT_WEIGHTS,
    HIGH_PRIORITY_CAP_WITHOUT_CONFIDENCE,
    MIN_CONFIDENCE_FOR_HIGH_PRIORITY,
)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def score_opportunity(
    *,
    opportunity: Opportunity | None,
    query: str,
    evidence: list[EvidenceRecord],
    pain_points: list[PainPoint],
    gap_report: GapReport | None,
    format_rec: FormatRecommendation | None,
) -> OpportunityScores:
    search = [e for e in evidence if e.kind is EvidenceKind.SEARCH]
    discussion = [e for e in evidence if e.kind is EvidenceKind.DISCUSSION]
    evidence_ids = [e.id for e in evidence if e.id is not None]
    opp_ids = list(opportunity.evidence_ids) if opportunity else evidence_ids[:20]
    if not opp_ids:
        opp_ids = evidence_ids[:20]

    # --- Demand Evidence ---
    demand_raw = 0.0
    demand_claims: list[LabeledClaim] = []
    if search:
        demand_raw += min(0.4, 0.08 * len(search))
        demand_claims.append(
            LabeledClaim(
                text=f"{len(search)} search evidence records present (not traffic volumes).",
                claim_tag=ClaimTag.MEASURED_FACT,
                evidence_ids=[e.id for e in search if e.id][:10],
            )
        )
    if discussion:
        demand_raw += min(0.35, 0.07 * len(discussion))
        demand_claims.append(
            LabeledClaim(
                text=f"{len(discussion)} discussion evidence records present.",
                claim_tag=ClaimTag.MEASURED_FACT,
                evidence_ids=[e.id for e in discussion if e.id][:10],
            )
        )
    if pain_points:
        demand_raw += min(0.25, 0.05 * len(pain_points))
        demand_claims.append(
            LabeledClaim(
                text=f"{len(pain_points)} extracted pain points (AI_INTERPRETATION of text).",
                claim_tag=ClaimTag.AI_INTERPRETATION,
                evidence_ids=[i for p in pain_points for i in p.evidence_ids][:10],
            )
        )
    if not evidence:
        demand_claims.append(
            LabeledClaim(
                text="No stored evidence — demand score forced low.",
                claim_tag=ClaimTag.MEASURED_FACT,
                evidence_ids=[],
            )
        )
        demand_raw = 0.0
    demand = ScoreExplanation(
        dimension=ScoreDimension.DEMAND_EVIDENCE,
        score=_clamp(demand_raw),
        weight=DEFAULT_WEIGHTS[ScoreDimension.DEMAND_EVIDENCE],
        explanation=(
            "Demand Evidence Score counts stored search/discussion/pain evidence only; "
            "it does not invent search volume or market-size figures."
        ),
        claims=demand_claims,
        evidence_ids=opp_ids[:20],
        inputs={
            "search_count": len(search),
            "discussion_count": len(discussion),
            "pain_point_count": len(pain_points),
        },
        limitations=["No Keyword Planner volumes unless a live provider returns them."],
    )

    # --- Organic Ranking Feasibility ---
    # Requires SERP-ish evidence; heuristic only.
    serp_items = [
        e
        for e in search
        if (e.provenance and e.provenance.source_url)
        or "serp" in (e.attributes or {}).get("source", "")
    ]
    # Mock SERP usually provides search records with URLs
    serp_with_url = [
        e for e in search if e.provenance and e.provenance.source_url
    ]
    organic_raw = 0.15
    organic_claims: list[LabeledClaim] = []
    if serp_with_url:
        organic_raw += min(0.45, 0.1 * len(serp_with_url))
        organic_claims.append(
            LabeledClaim(
                text=f"SERP-like results with URLs observed ({len(serp_with_url)}); feasibility is heuristic.",
                claim_tag=ClaimTag.AI_INTERPRETATION,
                evidence_ids=[e.id for e in serp_with_url if e.id][:10],
            )
        )
    else:
        organic_claims.append(
            LabeledClaim(
                text="No SERP URL observations — organic feasibility stays low.",
                claim_tag=ClaimTag.MEASURED_FACT,
                evidence_ids=[],
            )
        )
        organic_raw = 0.1
    if gap_report and any(
        c.status is CompetitorStatus.WEAKNESS_EVIDENCED for c in gap_report.competitors
    ):
        organic_raw += 0.15
        organic_claims.append(
            LabeledClaim(
                text="Evidenced competitor weaknesses may leave ranking room (hypothesis).",
                claim_tag=ClaimTag.HYPOTHESIS,
                evidence_ids=opp_ids[:10],
            )
        )
    organic = ScoreExplanation(
        dimension=ScoreDimension.ORGANIC_RANKING_FEASIBILITY,
        score=_clamp(organic_raw),
        weight=DEFAULT_WEIGHTS[ScoreDimension.ORGANIC_RANKING_FEASIBILITY],
        explanation=(
            "Organic Ranking Feasibility uses SERP observation presence and gap signals; "
            "weights are configurable heuristics, not predicted rankings."
        ),
        claims=organic_claims,
        evidence_ids=[e.id for e in serp_with_url if e.id][:20],
        inputs={"serp_url_count": len(serp_with_url), "serp_items": len(serp_items)},
        limitations=["No live SERP difficulty or Domain Authority measured in mock mode."],
    )

    # --- Format Fit ---
    format_raw = 0.2
    format_claims: list[LabeledClaim] = []
    primary: SolutionFormat | None = None
    if format_rec is not None:
        primary = format_rec.primary_format
        primary_eval = next(
            (e for e in format_rec.evaluations if e.format is primary), None
        )
        if primary_eval:
            format_raw = primary_eval.fit_score
            format_claims.extend(primary_eval.reasons_selected[:3])
        format_claims.append(
            LabeledClaim(
                text=f"Primary format hypothesis: {primary.value}.",
                claim_tag=ClaimTag.HYPOTHESIS,
                evidence_ids=list(format_rec.claims[0].evidence_ids)[:10]
                if format_rec.claims
                else opp_ids[:10],
            )
        )
    else:
        format_claims.append(
            LabeledClaim(
                text="No format recommendation run — format fit uses exploratory prior.",
                claim_tag=ClaimTag.AI_INTERPRETATION,
                evidence_ids=[],
            )
        )
    format_fit = ScoreExplanation(
        dimension=ScoreDimension.FORMAT_FIT,
        score=_clamp(format_raw),
        weight=DEFAULT_WEIGHTS[ScoreDimension.FORMAT_FIT],
        explanation="Format Fit mirrors the format recommender fit_score for the primary format.",
        claims=format_claims,
        evidence_ids=opp_ids[:20],
        inputs={"primary_format": primary.value if primary else None},
        limitations=["Format fit is a hypothesis, not proof users will adopt the format."],
    )

    # --- Business Viability ---
    biz_raw = 0.25
    biz_claims: list[LabeledClaim] = []
    if format_rec and primary:
        profile = FORMAT_CATALOG[primary]
        # Prefer simpler formats for early viability
        biz_raw += max(0.0, (15 - profile.default_preference_rank) * 0.03)
        if profile.monetization_hypotheses:
            biz_raw += 0.1
            biz_claims.append(
                LabeledClaim(
                    text=(
                        f"Monetization hypotheses for {profile.label}: "
                        + ", ".join(profile.monetization_hypotheses)
                    ),
                    claim_tag=ClaimTag.HYPOTHESIS,
                    evidence_ids=opp_ids[:10],
                )
            )
        biz_claims.append(
            LabeledClaim(
                text=(
                    f"Complexity={profile.complexity.value}, maintenance={profile.maintenance.value} "
                    "(catalog heuristic)."
                ),
                claim_tag=ClaimTag.AI_INTERPRETATION,
                evidence_ids=[],
            )
        )
    if gap_report and gap_report.findings:
        biz_raw += min(0.15, 0.05 * len(gap_report.findings))
        biz_claims.append(
            LabeledClaim(
                text=f"{len(gap_report.findings)} gap findings may indicate capture room (hypothesis).",
                claim_tag=ClaimTag.HYPOTHESIS,
                evidence_ids=opp_ids[:10],
            )
        )
    business = ScoreExplanation(
        dimension=ScoreDimension.BUSINESS_VIABILITY,
        score=_clamp(biz_raw),
        weight=DEFAULT_WEIGHTS[ScoreDimension.BUSINESS_VIABILITY],
        explanation=(
            "Business Viability combines format complexity/monetization hypotheses and gap signals; "
            "not a financial forecast."
        ),
        claims=biz_claims,
        evidence_ids=opp_ids[:20],
        inputs={},
        limitations=["No revenue, CAC, or LTV measurements available."],
    )

    # --- Evidence Confidence ---
    conf_raw = 0.0
    conf_claims: list[LabeledClaim] = []
    if evidence:
        conf_raw += min(0.5, 0.05 * len(evidence))
        providers = {e.provenance.provider for e in evidence if e.provenance}
        conf_raw += min(0.3, 0.1 * len(providers))
        conf_claims.append(
            LabeledClaim(
                text=f"{len(evidence)} evidence records from {len(providers)} providers.",
                claim_tag=ClaimTag.MEASURED_FACT,
                evidence_ids=evidence_ids[:20],
            )
        )
        if opportunity and opportunity.evidence_ids:
            conf_raw += 0.1
    else:
        conf_claims.append(
            LabeledClaim(
                text="Zero evidence records — confidence is 0.",
                claim_tag=ClaimTag.MEASURED_FACT,
                evidence_ids=[],
            )
        )
    confidence = ScoreExplanation(
        dimension=ScoreDimension.EVIDENCE_CONFIDENCE,
        score=_clamp(conf_raw),
        weight=DEFAULT_WEIGHTS[ScoreDimension.EVIDENCE_CONFIDENCE],
        explanation="Evidence Confidence reflects breadth of stored provenance, not claim truth.",
        claims=conf_claims,
        evidence_ids=evidence_ids[:20],
        inputs={"evidence_count": len(evidence)},
        limitations=["Mock providers reduce real-world confidence."],
    )

    # --- Overall Priority (never compensates for no evidence) ---
    components = [demand, organic, format_fit, business, confidence]
    weighted = sum(c.score * c.weight for c in components)
    overall_raw = weighted
    gate_note = ""
    if confidence.score < MIN_CONFIDENCE_FOR_HIGH_PRIORITY:
        overall_raw = min(overall_raw, HIGH_PRIORITY_CAP_WITHOUT_CONFIDENCE)
        gate_note = (
            f" Overall capped at {HIGH_PRIORITY_CAP_WITHOUT_CONFIDENCE} because "
            f"evidence_confidence={confidence.score:.2f} "
            f"< {MIN_CONFIDENCE_FOR_HIGH_PRIORITY}."
        )
    if confidence.score <= 0.0:
        overall_raw = 0.0
        gate_note = " Overall forced to 0 with no evidence confidence."

    overall = ScoreExplanation(
        dimension=ScoreDimension.OVERALL_PRIORITY,
        score=_clamp(overall_raw),
        weight=1.0,
        explanation=(
            "Overall Opportunity Priority is a weighted sum of independent dimensions "
            f"with inspectable weights { {k.value: v for k, v in DEFAULT_WEIGHTS.items()} }."
            + gate_note
            + " AI/format scores never replace missing evidence."
        ),
        claims=[
            LabeledClaim(
                text=f"Weighted overall={_clamp(overall_raw)}.{gate_note}",
                claim_tag=ClaimTag.AI_INTERPRETATION,
                evidence_ids=opp_ids[:20],
            )
        ],
        evidence_ids=opp_ids[:20],
        inputs={
            "weights": {k.value: v for k, v in DEFAULT_WEIGHTS.items()},
            "component_scores": {c.dimension.value: c.score for c in components},
        },
        limitations=["Priority is for ranking research, not investment advice."],
    )

    return OpportunityScores(
        demand_evidence=demand,
        organic_ranking_feasibility=organic,
        format_fit=format_fit,
        business_viability=business,
        evidence_confidence=confidence,
        overall_priority=overall,
    )
