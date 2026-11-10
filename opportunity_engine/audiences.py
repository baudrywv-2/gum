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

    # Discussion-heavy / search-light imbalance → possible underserved informational need
    if discussion and len(discussion) >= len(search):
        hypotheses.append(
            UnderservedAudienceHypothesis(
                audience_label=f"People discussing unresolved issues around {query}",
                geography=geography,
                language=language,
                rationale=(
                    f"Observed {len(discussion)} discussion evidence items vs "
                    f"{len(search)} search evidence items. Imbalance may indicate "
                    "unmet needs, but is not proof of market size."
                ),
                supporting_evidence_ids=discussion_ids[:20],
                claim_tag=ClaimTag.HYPOTHESIS,
                limitations=base_limitations
                + [
                    "Discussion volume from mock providers is synthetic in default config."
                ],
            )
        )

    if pain_points:
        top = sorted(pain_points, key=lambda p: -p.frequency)[:3]
        for pain in top:
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
