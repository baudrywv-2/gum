"""Underserved audience hypotheses — always labeled HYPOTHESIS, never demand fact."""

from __future__ import annotations

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceRecord, PainPoint
from packages.contracts.opportunities import UnderservedAudienceHypothesis


def hypothesize_underserved_audiences(
    *,
    query: str,
    geography: str | None,
    language: str | None,
    evidence: list[EvidenceRecord],
    pain_points: list[PainPoint],
) -> list[UnderservedAudienceHypothesis]:
    """Propose audience hypotheses from geo/lang + discussion-vs-search imbalance.

    These are explicitly HYPOTHESIS. Missing measured audience size is recorded.
    """
    hypotheses: list[UnderservedAudienceHypothesis] = []
    search = [e for e in evidence if e.kind.value == "search"]
    discussion = [e for e in evidence if e.kind.value == "discussion"]
    discussion_ids = [e.id for e in discussion if e.id is not None]

    base_limitations = [
        "Audience underservice is a HYPOTHESIS, not measured demand.",
        "No census, TAM, or traffic numbers were computed or fabricated.",
        "Validate with cheap experiments before building.",
    ]

    if geography or language:
        label_parts = []
        if geography:
            label_parts.append(f"geo:{geography}")
        if language:
            label_parts.append(f"lang:{language}")
        hypotheses.append(
            UnderservedAudienceHypothesis(
                audience_label=" / ".join(label_parts) + f" interested in {query}",
                geography=geography,
                language=language,
                rationale=(
                    "Query scoped to this geography/language. Discussion and pain-point "
                    "signals exist, but measured audience size is unknown."
                ),
                supporting_evidence_ids=discussion_ids[:20],
                claim_tag=ClaimTag.HYPOTHESIS,
                limitations=base_limitations
                + [
                    "Geography/language came from the discovery request, not measured reach."
                ],
            )
        )

    live_discussion = [
        e for e in discussion if e.provenance.provider_mode.value != "mock"
    ]
    mock_discussion = [
        e for e in discussion if e.provenance.provider_mode.value == "mock"
    ]
    live_search = [e for e in search if e.provenance.provider_mode.value != "mock"]

    # Discussion-heavy / search-light imbalance → possible underserved informational need
    if live_discussion and len(live_discussion) >= max(len(live_search), 1):
        live_ids = [e.id for e in live_discussion if e.id is not None]
        hypotheses.append(
            UnderservedAudienceHypothesis(
                audience_label=f"People discussing unresolved issues around {query}",
                geography=geography,
                language=language,
                rationale=(
                    f"Observed {len(live_discussion)} live discussion evidence items vs "
                    f"{len(live_search)} live search evidence items. Imbalance may indicate "
                    "unmet needs, but is not proof of market size."
                ),
                supporting_evidence_ids=live_ids[:20],
                claim_tag=ClaimTag.HYPOTHESIS,
                limitations=base_limitations
                + [
                    "Imbalance uses live discussion only; MOCK discussion excluded."
                ],
            )
        )
    elif not live_discussion and (mock_discussion or not discussion):
        hypotheses.append(
            UnderservedAudienceHypothesis(
                audience_label=f"Discussion signal unavailable for {query}",
                geography=geography,
                language=language,
                rationale=(
                    "Live discussion providers returned no usable posts (e.g. X unavailable). "
                    "Do not treat missing discussion as measured zero demand; prefer "
                    "SerpAPI/YouTube MEASURED_FACT search/video evidence for screening."
                ),
                supporting_evidence_ids=[e.id for e in live_search if e.id is not None][:20],
                claim_tag=ClaimTag.HYPOTHESIS,
                limitations=base_limitations
                + [
                    "Discussion unavailable or MOCK-only — not a live user-voice sample.",
                    "No synthetic discussion volume was substituted.",
                ],
            )
        )

    if pain_points:
        top = sorted(pain_points, key=lambda p: -p.frequency)[:3]
        for pain in top:
            providers = list(pain.source_providers or [])
            mock_only = providers and all(p.value == "mock" for p in providers)
            if mock_only:
                # Skip mock-only pains for audience cards — they dominate when X is down.
                continue
            hypotheses.append(
                UnderservedAudienceHypothesis(
                    audience_label=f"People experiencing: {pain.text[:80]}",
                    geography=geography,
                    language=language,
                    rationale=(
                        f"Recurring pain point (frequency={pain.frequency}) suggests a "
                        "segment with unresolved friction. Audience size unknown."
                    ),
                    supporting_evidence_ids=list(pain.evidence_ids)[:20],
                    claim_tag=ClaimTag.HYPOTHESIS,
                    limitations=base_limitations
                    + [
                        "Pain points are AI_INTERPRETATION extractions from discussion text."
                    ],
                )
            )

    # Deduplicate by audience_label
    seen: set[str] = set()
    unique: list[UnderservedAudienceHypothesis] = []
    for hyp in hypotheses:
        if hyp.audience_label in seen:
            continue
        seen.add(hyp.audience_label)
        unique.append(hyp)
    return unique
