"""Structured opportunity report generation, filter, and rank (Milestone 7)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from evidence.collector import EvidenceCollector
from evidence.store import EvidenceStore
from format_engine.recommend import FormatRecommender
from gap_engine.analyze import GapAnalysisEngine
from opportunity_engine.discover import OpportunityDiscoveryEngine
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import CollectEvidenceRequest, EvidenceKind
from packages.contracts.formats import RecommendFormatsRequest
from packages.contracts.gaps import AnalyzeGapsRequest, CompetitorStatus
from packages.contracts.opportunities import (
    DiscoverOpportunitiesRequest,
    LabeledClaim,
    Opportunity,
)
from packages.contracts.scoring import (
    GenerateReportRequest,
    GenerateReportResult,
    OpportunityReport,
    RankReportsRequest,
    ScoreDimension,
)
from providers.registry import ProviderRegistry, get_registry
from scoring_engine.score import score_opportunity
from scoring_engine.store import ScoringStore


class ReportEngine:
    def __init__(
        self,
        session: Session,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or get_registry()
        self.evidence_store = EvidenceStore(session)
        self.scoring_store = ScoringStore(session)
        self.collector = EvidenceCollector(session, registry=self.registry)
        self.discovery = OpportunityDiscoveryEngine(session, registry=self.registry)
        self.gaps = GapAnalysisEngine(session, registry=self.registry)
        self.formats = FormatRecommender(session, registry=self.registry)

    def generate(self, request: GenerateReportRequest) -> GenerateReportResult:
        limitations = [
            "Scores are transparent heuristics over stored evidence — not market forecasts.",
            "No search volumes, TAM, or competitor revenue were fabricated.",
            "Overall priority never compensates for missing evidence confidence.",
        ]

        collection_id = request.collection_id
        opportunities: list[Opportunity] = []
        gap_report = None
        format_rec = None
        gap_report_id = None
        format_recommendation_id = None

        if collection_id is None:
            if not request.collect_if_missing:
                raise ValueError("collection_id required when collect_if_missing=false")
            collected = self.collector.collect(
                CollectEvidenceRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                )
            )
            collection_id = collected.collection_id
            limitations.extend(collected.limitations)
        elif self.evidence_store.get_collection(collection_id) is None:
            raise ValueError(f"Unknown collection_id: {collection_id}")

        if request.run_discovery:
            discovered = self.discovery.discover(
                DiscoverOpportunitiesRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                    collection_id=collection_id,
                    collect_if_missing=False,
                )
            )
            opportunities = list(discovered.opportunities)
            limitations.extend(discovered.limitations)

        if request.run_gap_analysis:
            gap_result = self.gaps.analyze(
                AnalyzeGapsRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                    collection_id=collection_id,
                    collect_if_missing=False,
                )
            )
            gap_report = gap_result.report
            gap_report_id = gap_result.report_id
            limitations.extend(gap_result.limitations)

        if request.run_format_recommendation:
            format_result = self.formats.recommend(
                RecommendFormatsRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                    collection_id=collection_id,
                    collect_if_missing=False,
                    run_gap_analysis=False,
                )
            )
            format_rec = format_result.recommendation
            format_recommendation_id = format_result.recommendation_id
            limitations.extend(format_result.limitations)

        evidence = self.evidence_store.list_evidence(
            collection_id=collection_id, limit=500
        )
        pain_points = self.evidence_store.list_pain_points(
            collection_id=collection_id, limit=200
        )

        # If discovery found nothing, still emit one collection-level report.
        subjects: list[Opportunity | None] = list(opportunities) or [None]
        reports: list[OpportunityReport] = []

        for subject in subjects:
            scores = score_opportunity(
                opportunity=subject,
                query=request.query,
                evidence=evidence,
                pain_points=pain_points,
                gap_report=gap_report,
                format_rec=format_rec,
            )
            if scores.evidence_confidence.score < request.min_evidence_confidence:
                continue
            if scores.overall_priority.score < request.min_overall_priority:
                continue

            search = [e for e in evidence if e.kind is EvidenceKind.SEARCH]
            discussion = [e for e in evidence if e.kind is EvidenceKind.DISCUSSION]
            keywords = sorted(
                {
                    t
                    for e in search
                    for t in (e.title or "").lower().split()
                    if len(t) > 3
                }
            )[:20]

            competitor_names: list[str] = []
            weakness_claims: list[LabeledClaim] = []
            if gap_report:
                competitor_names = [c.name for c in gap_report.competitors]
                for competitor in gap_report.competitors:
                    if competitor.status is CompetitorStatus.WEAKNESS_EVIDENCED:
                        weakness_claims.extend(competitor.weaknesses[:3])

            unmet = [
                LabeledClaim(
                    text=p.text,
                    claim_tag=p.claim_tag,
                    evidence_ids=list(p.evidence_ids),
                )
                for p in pain_points[:10]
            ]

            primary_format = format_rec.primary_format if format_rec else None
            alt_formats = list(format_rec.alternatives) if format_rec else []
            primary_eval = None
            if format_rec and primary_format:
                primary_eval = next(
                    (e for e in format_rec.evaluations if e.format is primary_format),
                    None,
                )

            title = (
                subject.title
                if subject
                else f"Opportunity report: {request.query}"
            )
            summary = (
                subject.summary
                if subject
                else (
                    f"Structured report for '{request.query}' over collection "
                    f"{collection_id}."
                )
            )
            problem = subject.problem if subject else request.query
            audience = subject.audience if subject else None

            report = OpportunityReport(
                collection_id=collection_id,
                query=request.query,
                title=title,
                summary=summary,
                problem=problem,
                audience=audience,
                geography=request.geography or (subject.geography if subject else None),
                language=request.language or (subject.language if subject else None),
                demand_evidence=scores.demand_evidence.claims,
                search_behaviour_keywords=keywords,
                discussion_evidence=[
                    LabeledClaim(
                        text=e.summary or e.title,
                        claim_tag=e.provenance.claim_tag
                        if e.provenance
                        else ClaimTag.UNVERIFIED_CLAIM,
                        evidence_ids=[e.id] if e.id else [],
                    )
                    for e in discussion[:10]
                ],
                competitors=competitor_names,
                competitor_weaknesses=weakness_claims,
                unmet_needs=unmet,
                recommended_format=primary_format,
                alternative_formats=alt_formats,
                scores=scores,
                complexity=primary_eval.complexity.value if primary_eval else None,
                build_maintenance=(
                    f"maintenance={primary_eval.maintenance.value}"
                    if primary_eval
                    else None
                ),
                monetization_hypotheses=(
                    list(primary_eval.monetization_hypotheses) if primary_eval else []
                ),
                risks=[
                    LabeledClaim(
                        text="Mock-provider evidence may not reflect live markets.",
                        claim_tag=ClaimTag.AI_INTERPRETATION,
                        evidence_ids=[],
                    )
                ],
                source_urls=[
                    e.provenance.source_url
                    for e in evidence
                    if e.provenance and e.provenance.source_url
                ][:30],
                timestamps={
                    "collected_at": evidence[0].provenance.collected_at
                    if evidence and evidence[0].provenance
                    else None
                },
                limitations=list(
                    dict.fromkeys(
                        limitations
                        + (subject.limitations if subject else [])
                        + scores.overall_priority.limitations
                    )
                ),
                contradictions=[],
                missing_info=[
                    "Live Keyword Planner volumes",
                    "Measured conversion by format",
                    "Independent competitor financials",
                    *(subject.missing_info if subject else []),
                ],
                cheapest_validation_experiment=(
                    primary_eval.cheapest_validation if primary_eval else None
                ),
                next_actions=[
                    "Review labeled claims against source evidence",
                    "Run cheapest validation experiment before building",
                    "Re-score after live provider data if credentials exist",
                ],
                claims=[
                    LabeledClaim(
                        text=(
                            f"Overall priority={scores.overall_priority.score:.2f} "
                            f"(inspectable weighted dimensions)."
                        ),
                        claim_tag=ClaimTag.AI_INTERPRETATION,
                        evidence_ids=list(scores.overall_priority.evidence_ids),
                    )
                ],
                evidence_ids=list(subject.evidence_ids)
                if subject and subject.evidence_ids
                else [e.id for e in evidence if e.id][:40],
                opportunity_ids=[subject.id] if subject and subject.id else [],
                format_recommendation_id=format_recommendation_id,
                gap_report_id=gap_report_id,
            )
            saved = self.scoring_store.save_report(report)
            reports.append(saved)

        self.session.commit()
        ranked = self._rank(
            reports,
            rank_by=request.rank_by,
            min_evidence_confidence=request.min_evidence_confidence,
            min_overall_priority=request.min_overall_priority,
            limit=request.limit,
        )
        return GenerateReportResult(
            reports=ranked,
            collection_id=collection_id,
            query=request.query,
            ranked_by=request.rank_by,
            count=len(ranked),
            limitations=list(dict.fromkeys(limitations)),
        )

    def rank_existing(self, request: RankReportsRequest) -> list[OpportunityReport]:
        if request.report_ids:
            reports = [
                r
                for rid in request.report_ids
                if (r := self.scoring_store.get_report(rid)) is not None
            ]
        else:
            reports = self.scoring_store.list_reports(limit=200)
        return self._rank(
            reports,
            rank_by=request.rank_by,
            min_evidence_confidence=request.min_evidence_confidence,
            min_overall_priority=request.min_overall_priority,
            limit=request.limit,
        )

    @staticmethod
    def _rank(
        reports: list[OpportunityReport],
        *,
        rank_by: ScoreDimension,
        min_evidence_confidence: float,
        min_overall_priority: float,
        limit: int,
    ) -> list[OpportunityReport]:
        filtered: list[OpportunityReport] = []
        for report in reports:
            if report.scores.evidence_confidence.score < min_evidence_confidence:
                continue
            if report.scores.overall_priority.score < min_overall_priority:
                continue
            filtered.append(report)

        def key(report: OpportunityReport) -> float:
            mapping = {
                ScoreDimension.DEMAND_EVIDENCE: report.scores.demand_evidence.score,
                ScoreDimension.ORGANIC_RANKING_FEASIBILITY: report.scores.organic_ranking_feasibility.score,
                ScoreDimension.FORMAT_FIT: report.scores.format_fit.score,
                ScoreDimension.BUSINESS_VIABILITY: report.scores.business_viability.score,
                ScoreDimension.EVIDENCE_CONFIDENCE: report.scores.evidence_confidence.score,
                ScoreDimension.OVERALL_PRIORITY: report.scores.overall_priority.score,
            }
            return mapping[rank_by]

        filtered.sort(key=key, reverse=True)
        return filtered[:limit]
