"""Competitor and gap analysis orchestrator (Milestone 5)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from evidence.collector import EvidenceCollector
from evidence.store import EvidenceStore
from gap_engine.competitors import extract_competitors
from gap_engine.gaps import (
    attach_feedback_to_competitors,
    competitor_weakness_findings,
    find_missing_feature_gaps,
    search_vs_feedback_summary,
)
from gap_engine.store import GapStore
from packages.contracts.evidence import CollectEvidenceRequest, EvidenceKind
from packages.contracts.gaps import AnalyzeGapsRequest, AnalyzeGapsResult, GapReport
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.claim_tags import ClaimTag
from providers.registry import ProviderRegistry, get_registry


class GapAnalysisEngine:
    def __init__(
        self,
        session: Session,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or get_registry()
        self.evidence_store = EvidenceStore(session)
        self.gap_store = GapStore(session)
        self.collector = EvidenceCollector(session, registry=self.registry)

    def analyze(self, request: AnalyzeGapsRequest) -> AnalyzeGapsResult:
        limitations = [
            "Gap analysis uses mock/stub providers unless live clients are explicitly enabled.",
            "No competitor is labeled weak without discussion evidence containing complaint cues.",
            "No demand volumes or market-share figures were fabricated.",
        ]

        collection_id = request.collection_id
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

        evidence = self.evidence_store.list_evidence(
            collection_id=collection_id, limit=500
        )
        pain_points = self.evidence_store.list_pain_points(
            collection_id=collection_id, limit=200
        )
        search = [e for e in evidence if e.kind is EvidenceKind.SEARCH]
        discussion = [e for e in evidence if e.kind is EvidenceKind.DISCUSSION]

        if not evidence:
            limitations.append(
                "No stored evidence for this collection; empty gap report returned."
            )
            report = GapReport(
                collection_id=collection_id,
                query=request.query,
                geography=request.geography,
                language=request.language,
                search_vs_feedback="No evidence available.",
                claims=[
                    LabeledClaim(
                        text="No evidence available for gap analysis.",
                        claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                        evidence_ids=[],
                    )
                ],
                missing_info=["Search evidence", "Discussion evidence"],
                limitations=list(dict.fromkeys(limitations)),
            )
            saved = self.gap_store.save_report(report)
            self.session.commit()
            return AnalyzeGapsResult(
                report_id=saved.id,
                collection_id=collection_id,
                query=request.query,
                report=saved,
                limitations=saved.limitations,
            )

        competitors = extract_competitors(
            evidence, max_competitors=request.max_competitors
        )
        competitors = attach_feedback_to_competitors(competitors, evidence)

        findings = []
        findings.extend(
            find_missing_feature_gaps(
                pain_points=pain_points,
                search_evidence=search,
                max_findings=request.max_findings,
            )
        )
        findings.extend(competitor_weakness_findings(competitors))
        findings = findings[: request.max_findings]

        summary, summary_claims = search_vs_feedback_summary(
            search_count=len(search),
            discussion_count=len(discussion),
            competitors=competitors,
            gap_count=len(findings),
        )

        report = GapReport(
            collection_id=collection_id,
            query=request.query,
            geography=request.geography,
            language=request.language,
            competitors=competitors,
            findings=findings,
            search_vs_feedback=summary,
            claims=summary_claims,
            missing_info=[
                "Live SERP crawl of named competitors",
                "Product teardown / feature inventory",
                "Measured market share",
                "Independent verification of alleged weaknesses",
            ],
            limitations=list(dict.fromkeys(limitations)),
        )
        saved = self.gap_store.save_report(report)
        self.session.commit()
        return AnalyzeGapsResult(
            report_id=saved.id,
            collection_id=collection_id,
            query=request.query,
            report=saved,
            limitations=saved.limitations,
        )
