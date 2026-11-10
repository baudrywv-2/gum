"""Opportunity discovery orchestrator (Milestone 4).

Production rules:
- Every opportunity claim is labeled (MEASURED/ESTIMATE/AI_INTERPRETATION/HYPOTHESIS/UNVERIFIED).
- Opportunities are grounded in stored evidence IDs when available.
- Never fabricate demand volumes, TAM, or conversion rates.
- Prefer transparent missing_info over opaque scores.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from evidence.collector import EvidenceCollector
from evidence.store import EvidenceStore
from opportunity_engine.audiences import hypothesize_underserved_audiences
from opportunity_engine.cluster import cluster_evidence, correlate_clusters
from opportunity_engine.store import OpportunityStore
from opportunity_engine.themes import detect_emerging_themes
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import CollectEvidenceRequest
from packages.contracts.opportunities import (
    DiscoverOpportunitiesRequest,
    DiscoverOpportunitiesResult,
    LabeledClaim,
    Opportunity,
    OpportunityType,
)
from providers.registry import ProviderRegistry, get_registry

_COMMON_MISSING = [
    "Measured search volume / demand",
    "Willingness to pay",
    "Audience size",
    "Competitive coverage (Milestone 5+)",
]


class OpportunityDiscoveryEngine:
    def __init__(
        self,
        session: Session,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or get_registry()
        self.evidence_store = EvidenceStore(session)
        self.opportunity_store = OpportunityStore(session)
        self.collector = EvidenceCollector(session, registry=self.registry)

    def discover(
        self, request: DiscoverOpportunitiesRequest
    ) -> DiscoverOpportunitiesResult:
        limitations = [
            "Prefer SerpAPI/YouTube MEASURED_FACT search/video evidence over MOCK discussion.",
            "No demand volumes, TAM, or conversion rates were fabricated.",
            "Interpretive outputs are claim-tagged; treat HYPOTHESIS/AI_INTERPRETATION as non-factual.",
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
        if not evidence:
            limitations.append(
                "No stored evidence for this collection; discovery returned no opportunities "
                "rather than inventing signals."
            )
            run = self.opportunity_store.create_run(
                collection_id=collection_id,
                query=request.query,
                geography=request.geography,
                language=request.language,
            )
            self.session.commit()
            return DiscoverOpportunitiesResult(
                run_id=run.id,
                collection_id=collection_id,
                query=request.query,
                limitations=list(dict.fromkeys(limitations)),
            )

        pain_points = self.evidence_store.list_pain_points(
            collection_id=collection_id, limit=200
        )

        clusters = cluster_evidence(
            evidence, min_cluster_size=request.min_cluster_size
        )
        if not clusters and evidence:
            clusters = cluster_evidence(evidence, min_cluster_size=1)[:10]
            limitations.append(
                "Few related evidence pairs met the cluster threshold; "
                "singleton clusters included for inspectability only."
            )

        themes = detect_emerging_themes(evidence)
        correlations = correlate_clusters(clusters, evidence)

        live_evidence = [
            e
            for e in evidence
            if e.provenance.provider_mode.value == "live"
            and e.provenance.claim_tag is ClaimTag.MEASURED_FACT
        ]
        if live_evidence:
            limitations.append(
                f"Live MEASURED_FACT evidence items in collection: {len(live_evidence)} "
                "(SerpAPI/YouTube/etc.) — weight these above MOCK discussion."
            )

        live_backed_pains = [
            p
            for p in pain_points
            if p.source_providers
            and not all(prov.value == "mock" for prov in p.source_providers)
        ]
        mock_only_pains = [
            p
            for p in pain_points
            if p.source_providers
            and all(prov.value == "mock" for prov in p.source_providers)
        ]
        if mock_only_pains:
            limitations.append(
                f"Skipped {len(mock_only_pains)} MOCK-only pain point(s) when building "
                "opportunity cards (discussion synthetic / not live user voice)."
            )
        if not any(e.kind.value == "discussion" and e.provenance.provider_mode.value == "live" for e in evidence):
            limitations.append(
                "Live discussion unavailable; recurring-problem cards from discussion "
                "pain are omitted or labeled hypothesis only."
            )

        audiences = hypothesize_underserved_audiences(
            query=request.query,
            geography=request.geography,
            language=request.language,
            evidence=evidence,
            pain_points=live_backed_pains,
        )

        # Prefer live MEASURED_FACT themes/correlations before weaker pain/audience cards.
        themes_sorted = sorted(
            themes,
            key=lambda t: (
                -sum(1 for p in t.providers if p.value in {"serp", "youtube", "google_trends"}),
                -t.provider_count,
                -t.evidence_count,
            ),
        )
        buckets = [
            self._from_themes(themes_sorted, request),
            self._from_correlations(correlations, request),
            self._from_pain_points(live_backed_pains, request),
            self._from_audiences(audiences, request),
        ]
        opportunities = self._interleave(buckets, request.max_opportunities)

        run = self.opportunity_store.create_run(
            collection_id=collection_id,
            query=request.query,
            geography=request.geography,
            language=request.language,
        )

        saved_clusters = [
            self.opportunity_store.save_cluster(run_id=run.id, cluster=cluster)
            for cluster in clusters
        ]
        saved_opportunities: list[Opportunity] = []
        for opp in opportunities:
            opp.run_id = run.id
            opp.collection_id = collection_id
            saved_opportunities.append(self.opportunity_store.save_opportunity(opp))

        self.session.commit()

        recurring = [
            o
            for o in saved_opportunities
            if o.opportunity_type is OpportunityType.RECURRING_PROBLEM
        ]

        return DiscoverOpportunitiesResult(
            run_id=run.id,
            collection_id=collection_id,
            query=request.query,
            clusters=saved_clusters,
            recurring_problems=recurring,
            emerging_themes=themes_sorted,
            underserved_audiences=audiences,
            correlations=correlations,
            opportunities=saved_opportunities,
            limitations=list(dict.fromkeys(limitations)),
        )

    @staticmethod
    def _interleave(
        buckets: list[list[Opportunity]], limit: int
    ) -> list[Opportunity]:
        selected: list[Opportunity] = []
        indexes = [0] * len(buckets)
        while len(selected) < limit:
            progressed = False
            for i, bucket in enumerate(buckets):
                if indexes[i] >= len(bucket):
                    continue
                selected.append(bucket[indexes[i]])
                indexes[i] += 1
                progressed = True
                if len(selected) >= limit:
                    break
            if not progressed:
                break
        return selected

    @staticmethod
    def _from_pain_points(pain_points, request: DiscoverOpportunitiesRequest) -> list[Opportunity]:
        out: list[Opportunity] = []
        for pain in sorted(pain_points, key=lambda p: -p.frequency):
            evidence_ids = list(pain.evidence_ids)
            out.append(
                Opportunity(
                    opportunity_type=OpportunityType.RECURRING_PROBLEM,
                    title=f"Recurring problem: {pain.text[:100]}",
                    summary=(
                        f"Extracted pain point appears {pain.frequency} time(s) in this "
                        f"collection across {len(pain.source_providers)} provider(s). "
                        "Frequency is collection-local, not market prevalence."
                    ),
                    problem=pain.text,
                    geography=request.geography,
                    language=request.language,
                    claims=[
                        LabeledClaim(
                            text=pain.text,
                            claim_tag=ClaimTag.AI_INTERPRETATION,
                            evidence_ids=evidence_ids,
                        ),
                        LabeledClaim(
                            text=(
                                f"Collection-local recurrence count={pain.frequency} "
                                "(not measured demand)"
                            ),
                            claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                            evidence_ids=evidence_ids,
                        ),
                    ],
                    evidence_ids=evidence_ids,
                    providers=list(pain.source_providers),
                    missing_info=list(_COMMON_MISSING),
                    limitations=list(pain.limitations)
                    + [
                        "Pain-point text is heuristically extracted (AI_INTERPRETATION).",
                        "Do not treat recurrence count as search volume or TAM.",
                    ],
                    attributes={"pain_frequency": pain.frequency},
                )
            )
        return out

    @staticmethod
    def _from_themes(themes, request: DiscoverOpportunitiesRequest) -> list[Opportunity]:
        out: list[Opportunity] = []
        for theme in themes:
            out.append(
                Opportunity(
                    opportunity_type=OpportunityType.EMERGING_THEME,
                    title=theme.theme,
                    summary=(
                        f"Token '{theme.token}' co-occurs in {theme.evidence_count} stored "
                        f"evidence items across {theme.provider_count} providers. "
                        "Lexical signal only — no demand estimate attached."
                    ),
                    problem=(
                        f"Possible emerging theme around '{theme.token}' related to "
                        f"{request.query}"
                    ),
                    geography=request.geography,
                    language=request.language,
                    claims=[
                        LabeledClaim(
                            text=(
                                f"Multi-provider lexical theme '{theme.token}' "
                                f"(providers={theme.provider_count}, evidence={theme.evidence_count})"
                            ),
                            claim_tag=ClaimTag.AI_INTERPRETATION,
                            evidence_ids=list(theme.evidence_ids),
                        )
                    ],
                    evidence_ids=list(theme.evidence_ids),
                    providers=list(theme.providers),
                    themes=[theme.token],
                    missing_info=list(_COMMON_MISSING)
                    + ["Trend confirmation with live providers"],
                    limitations=list(theme.limitations),
                    attributes={
                        "token": theme.token,
                        "evidence_count": theme.evidence_count,
                        "provider_count": theme.provider_count,
                    },
                )
            )
        return out

    @staticmethod
    def _from_audiences(audiences, request: DiscoverOpportunitiesRequest) -> list[Opportunity]:
        out: list[Opportunity] = []
        for audience in audiences:
            evidence_ids = list(audience.supporting_evidence_ids)
            out.append(
                Opportunity(
                    opportunity_type=OpportunityType.UNDERSERVED_AUDIENCE,
                    title=f"Possible underserved audience: {audience.audience_label}",
                    summary=audience.rationale,
                    problem=f"Potential unmet needs for {audience.audience_label}",
                    audience=audience.audience_label,
                    geography=audience.geography or request.geography,
                    language=audience.language or request.language,
                    claims=[
                        LabeledClaim(
                            text=audience.rationale,
                            claim_tag=ClaimTag.HYPOTHESIS,
                            evidence_ids=evidence_ids,
                        )
                    ],
                    evidence_ids=evidence_ids,
                    providers=[],
                    missing_info=list(_COMMON_MISSING) + ["Channel reach"],
                    limitations=list(audience.limitations),
                    attributes={},
                )
            )
        return out

    @staticmethod
    def _from_correlations(correlations, request: DiscoverOpportunitiesRequest) -> list[Opportunity]:
        out: list[Opportunity] = []
        for corr in correlations:
            evidence_ids = list(corr.evidence_ids)
            provider_names = ", ".join(p.value for p in corr.providers)
            out.append(
                Opportunity(
                    opportunity_type=OpportunityType.CROSS_SOURCE,
                    title=f"Cross-source signal: {corr.cluster_label}",
                    summary=(
                        f"Related stored evidence spans providers [{provider_names}] "
                        f"(search={corr.search_count}, discussion={corr.discussion_count}). "
                        "Correlation is interpretive, not causal demand proof."
                    ),
                    problem=f"Correlated signals around {corr.cluster_label}",
                    geography=request.geography,
                    language=request.language,
                    claims=[
                        LabeledClaim(
                            text=(
                                "Independent sources share related tokens in stored evidence; "
                                "not proof of market size."
                            ),
                            claim_tag=ClaimTag.AI_INTERPRETATION,
                            evidence_ids=evidence_ids,
                        )
                    ],
                    evidence_ids=evidence_ids,
                    providers=list(corr.providers),
                    themes=[corr.cluster_label],
                    missing_info=list(_COMMON_MISSING)
                    + ["Causal link between sources"],
                    limitations=list(corr.limitations),
                    attributes={
                        "search_count": corr.search_count,
                        "discussion_count": corr.discussion_count,
                    },
                )
            )
        return out
