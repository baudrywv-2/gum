"""Format recommendation orchestrator (Milestone 6).

Rules:
- Recommendations are hypotheses grounded in stored evidence.
- Do not auto-recommend a website; SEO blog must earn fit from signals.
- Prefer simpler formats when scores are close.
- Never fabricate demand volumes.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from evidence.collector import EvidenceCollector
from evidence.store import EvidenceStore
from format_engine.catalog import FORMAT_CATALOG, all_formats
from format_engine.signals import FormatSignals, build_signals
from format_engine.store import FormatStore
from gap_engine.analyze import GapAnalysisEngine
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import CollectEvidenceRequest
from packages.contracts.formats import (
    FormatDecision,
    FormatEvaluation,
    FormatRecommendation,
    RecommendFormatsRequest,
    RecommendFormatsResult,
    SolutionFormat,
)
from packages.contracts.gaps import AnalyzeGapsRequest
from packages.contracts.opportunities import LabeledClaim
from providers.registry import ProviderRegistry, get_registry

class FormatRecommender:
    def __init__(
        self,
        session: Session,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or get_registry()
        self.evidence_store = EvidenceStore(session)
        self.format_store = FormatStore(session)
        self.collector = EvidenceCollector(session, registry=self.registry)
        self.gap_engine = GapAnalysisEngine(session, registry=self.registry)

    def recommend(self, request: RecommendFormatsRequest) -> RecommendFormatsResult:
        limitations = [
            "Format recommendations are hypotheses (not prescriptions).",
            "Fit scores are transparent heuristics over stored evidence — not demand forecasts.",
            "No TAM, traffic, or revenue figures were fabricated.",
            "Simpler formats are preferred when evidence support is similar.",
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

        gap_report = None
        if request.run_gap_analysis:
            gap_result = self.gap_engine.analyze(
                AnalyzeGapsRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                    collection_id=collection_id,
                    collect_if_missing=False,
                )
            )
            gap_report = gap_result.report
            limitations.extend(gap_result.limitations)

        signals = build_signals(
            query=request.query,
            evidence=evidence,
            pain_points=pain_points,
            gap_report=gap_report,
        )

        scored = [self._evaluate(fmt.format, signals) for fmt in all_formats()]
        scored.sort(
            key=lambda e: (
                -e.fit_score,
                FORMAT_CATALOG[e.format].default_preference_rank,
            )
        )

        primary = scored[0]
        # Guard: do not auto-pick SEO website if another simpler format is within bias
        # and website was not specifically supported.
        primary = self._apply_anti_default_website(primary, scored, signals)

        alternatives: list[FormatEvaluation] = []
        complementary: list[FormatEvaluation] = []
        rejected: list[FormatEvaluation] = []

        for evaluation in scored:
            if evaluation.format is primary.format:
                evaluation.decision = FormatDecision.PRIMARY
                continue
            if (
                evaluation.fit_score >= max(0.35, primary.fit_score - 0.2)
                and len(alternatives) < request.max_alternatives
            ):
                evaluation.decision = FormatDecision.ALTERNATIVE
                alternatives.append(evaluation)
            elif (
                evaluation.fit_score >= 0.25
                and self._is_complementary(primary.format, evaluation.format)
                and len(complementary) < request.max_complementary
            ):
                evaluation.decision = FormatDecision.COMPLEMENTARY
                complementary.append(evaluation)
            else:
                evaluation.decision = FormatDecision.REJECTED
                if not evaluation.reasons_rejected:
                    evaluation.reasons_rejected.append(
                        LabeledClaim(
                            text=(
                                f"{FORMAT_CATALOG[evaluation.format].label} fit_score="
                                f"{evaluation.fit_score:.2f} below selection thresholds "
                                f"or dominated by simpler options."
                            ),
                            claim_tag=ClaimTag.AI_INTERPRETATION,
                            evidence_ids=list(evaluation.evidence_ids)[:10],
                        )
                    )
                rejected.append(evaluation)

        evaluations = [primary, *alternatives, *complementary, *rejected]
        summary = (
            f"Primary recommendation: {FORMAT_CATALOG[primary.format].label} "
            f"(fit_score={primary.fit_score:.2f}). "
            f"Alternatives: {', '.join(FORMAT_CATALOG[a.format].label for a in alternatives) or 'none'}. "
            "All recommendations are hypotheses grounded in collected evidence signals."
        )

        recommendation = FormatRecommendation(
            collection_id=collection_id,
            query=request.query,
            geography=request.geography,
            language=request.language,
            primary_format=primary.format,
            alternatives=[a.format for a in alternatives],
            complementary=[c.format for c in complementary],
            rejected=[r.format for r in rejected],
            evaluations=evaluations,
            summary=summary,
            claims=[
                LabeledClaim(
                    text=summary,
                    claim_tag=ClaimTag.HYPOTHESIS,
                    evidence_ids=list(signals.evidence_ids)[:20],
                )
            ],
            missing_info=[
                "Measured conversion by format",
                "Channel-specific audience reach",
                "Build/run cost quotes",
                "Live competitive format inventory",
            ],
            limitations=list(dict.fromkeys(limitations)),
        )
        saved = self.format_store.save_recommendation(recommendation)
        self.session.commit()
        return RecommendFormatsResult(
            recommendation_id=saved.id,
            collection_id=collection_id,
            query=request.query,
            recommendation=saved,
            limitations=saved.limitations,
        )

    def _apply_anti_default_website(
        self,
        primary: FormatEvaluation,
        scored: list[FormatEvaluation],
        signals: FormatSignals,
    ) -> FormatEvaluation:
        if primary.format is not SolutionFormat.SEO_WEBSITE_BLOG:
            return primary
        # If website wasn't strongly content-supported, prefer best non-website nearby.
        if "contentish" in signals.flags and signals.search_heavy:
            return primary
        for candidate in scored[1:]:
            if candidate.format is SolutionFormat.SEO_WEBSITE_BLOG:
                continue
            if primary.fit_score - candidate.fit_score <= 0.15:
                primary.decision = FormatDecision.ALTERNATIVE
                primary.reasons_rejected.append(
                    LabeledClaim(
                        text=(
                            "SEO website/blog was not auto-selected; a simpler or better-fitting "
                            "format was within the evidence margin."
                        ),
                        claim_tag=ClaimTag.AI_INTERPRETATION,
                        evidence_ids=list(signals.evidence_ids)[:10],
                    )
                )
                return candidate
        return primary

    @staticmethod
    def _is_complementary(primary: SolutionFormat, other: SolutionFormat) -> bool:
        pairs = {
            SolutionFormat.CALCULATOR_TOOL: {
                SolutionFormat.SEO_WEBSITE_BLOG,
                SolutionFormat.NEWSLETTER_ALERTS,
                SolutionFormat.YOUTUBE,
            },
            SolutionFormat.SEO_WEBSITE_BLOG: {
                SolutionFormat.NEWSLETTER_ALERTS,
                SolutionFormat.YOUTUBE,
                SolutionFormat.CALCULATOR_TOOL,
            },
            SolutionFormat.SAAS: {
                SolutionFormat.SEO_WEBSITE_BLOG,
                SolutionFormat.YOUTUBE,
                SolutionFormat.API_DATA_SERVICE,
            },
            SolutionFormat.WEB_APP: {
                SolutionFormat.SEO_WEBSITE_BLOG,
                SolutionFormat.NEWSLETTER_ALERTS,
            },
            SolutionFormat.DIRECTORY: {
                SolutionFormat.SEO_WEBSITE_BLOG,
                SolutionFormat.NEWSLETTER_ALERTS,
            },
        }
        return other in pairs.get(primary, set())

    def _evaluate(
        self, fmt: SolutionFormat, signals: FormatSignals
    ) -> FormatEvaluation:
        profile = FORMAT_CATALOG[fmt]
        score = 0.15  # base exploratory prior (not demand)
        reasons_for: list[LabeledClaim] = []
        reasons_against: list[LabeledClaim] = []
        evidence_ids = list(signals.pain_evidence_ids or signals.evidence_ids)[:20]

        def add(delta: float, text: str, tag: ClaimTag = ClaimTag.AI_INTERPRETATION) -> None:
            nonlocal score
            score += delta
            bucket = reasons_for if delta >= 0 else reasons_against
            bucket.append(
                LabeledClaim(text=text, claim_tag=tag, evidence_ids=evidence_ids)
            )

        # Signal-based fit
        if fmt is SolutionFormat.CALCULATOR_TOOL:
            if "toolish" in signals.flags or "gap_signal" in signals.flags:
                add(0.35, "Tool/gap language in evidence supports a calculator/tool.")
            if signals.discussion_heavy:
                add(0.1, "Discussion-heavy collection suits a focused tool MVP.")
            if "saasish" in signals.flags:
                add(-0.05, "SaaS-like language present; tool may be too narrow (still often cheaper to validate).")

        elif fmt is SolutionFormat.NEWSLETTER_ALERTS:
            if "newsletterish" in signals.flags or signals.discussion_heavy:
                add(0.3, "Recurring discussion/alerts intent supports a newsletter hypothesis.")
            if signals.pain_point_count:
                add(0.1, "Pain points can seed digest topics without building software first.")

        elif fmt is SolutionFormat.SEO_WEBSITE_BLOG:
            if "contentish" in signals.flags and signals.search_heavy:
                add(0.32, "Search-heavy + guide/how-to language supports SEO content (hypothesis).")
            elif "contentish" in signals.flags:
                add(0.18, "Some content language present, but search is not dominant.")
            else:
                add(-0.05, "No strong content/search pattern — website not auto-favored.")
            if signals.search_count == 0:
                add(-0.15, "No search evidence in collection to justify SEO-first.")

        elif fmt is SolutionFormat.YOUTUBE:
            if "videoish" in signals.flags or "contentish" in signals.flags:
                add(0.28, "Explain/tutorial signals support YouTube as a format hypothesis.")
            if signals.discussion_heavy:
                add(0.08, "Discussion themes can become video scripts.")

        elif fmt is SolutionFormat.DIRECTORY:
            if "directoryish" in signals.flags:
                add(0.34, "Comparison/list/alternatives language supports a directory.")
            if signals.evidenced_competitor_weaknesses:
                add(0.1, "Multiple competitor mentions may fit a curated alternatives directory.")

        elif fmt is SolutionFormat.DIGITAL_PRODUCT:
            if "toolish" in signals.flags or "unmet_need" in signals.flags:
                add(0.25, "Template/pack may satisfy unmet need cheaper than software.")
            else:
                add(0.05, "Digital product remains a low-complexity fallback.")

        elif fmt is SolutionFormat.WEB_APP:
            if "saasish" in signals.flags or "toolish" in signals.flags:
                add(0.22, "Interactive workflow signals could justify a web app — still validate simply first.")
            add(-0.08, "Higher complexity than calculator/newsletter; needs stronger evidence.")

        elif fmt is SolutionFormat.SAAS:
            if "saasish" in signals.flags or signals.evidenced_competitor_weaknesses:
                add(0.24, "Competitor-tool friction may support a SaaS hypothesis.")
            add(-0.12, "SaaS complexity/maintenance is high; prefer simpler validation first.")

        elif fmt is SolutionFormat.API_DATA_SERVICE:
            if "apiish" in signals.flags:
                add(0.3, "API/integration language supports an API/data service hypothesis.")
            else:
                add(-0.1, "Little API-specific evidence.")

        elif fmt is SolutionFormat.MARKETPLACE:
            if "marketplaceish" in signals.flags:
                add(0.25, "Marketplace language detected — still very high complexity.")
            add(-0.2, "Two-sided marketplaces are expensive; reject unless evidence is strong.")

        elif fmt is SolutionFormat.AI_AGENT:
            if "agentish" in signals.flags or "toolish" in signals.flags:
                add(0.2, "Automation language could support an agent — validate with human-in-the-loop first.")
            add(-0.1, "Agents are complex to maintain; not preferred by default.")

        elif fmt in {SolutionFormat.ANDROID_APP, SolutionFormat.IOS_APP}:
            if "mobileish" in signals.flags:
                add(0.3, "Explicit mobile language supports native app consideration.")
            else:
                add(-0.25, "No mobile-specific evidence — native apps rejected by default.")

        elif fmt is SolutionFormat.PROFESSIONAL_SERVICES:
            if "servicesish" in signals.flags or signals.discussion_heavy:
                add(0.22, "Service/done-for-you language or discussion intensity supports a services pilot.")
            add(0.05, "Services are often the cheapest way to learn before productizing.")

        # Prefer simple: small bonus inversely related to complexity rank
        score += max(0.0, (15 - profile.default_preference_rank) * 0.005)
        score = max(0.0, min(1.0, score))

        # Near-tie simplicity nudge recorded transparently
        if profile.default_preference_rank <= 3:
            reasons_for.append(
                LabeledClaim(
                    text=(
                        f"{profile.label} is relatively simple "
                        f"(complexity={profile.complexity.value}); preferred when evidence is similar."
                    ),
                    claim_tag=ClaimTag.AI_INTERPRETATION,
                    evidence_ids=evidence_ids,
                )
            )

        return FormatEvaluation(
            format=fmt,
            decision=FormatDecision.REJECTED,  # set later
            fit_score=round(score, 3),
            complexity=profile.complexity,
            maintenance=profile.maintenance,
            monetization_hypotheses=list(profile.monetization_hypotheses),
            cheapest_validation=profile.cheapest_validation,
            reasons_selected=reasons_for,
            reasons_rejected=reasons_against,
            evidence_ids=evidence_ids,
            missing_info=[
                "Format-specific conversion evidence",
                "Build cost quote",
            ],
            limitations=[
                "Fit score is a heuristic over lexical/evidence signals, not measured demand.",
            ],
            attributes={
                "preference_rank": profile.default_preference_rank,
                "flags": sorted(signals.flags),
            },
        )
