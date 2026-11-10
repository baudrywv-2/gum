"""Evidence-backed gap findings — never invent competitor weaknesses."""

from __future__ import annotations

import re
from uuid import uuid4

from evidence.dedupe import normalize_text
from opportunity_engine.tokens import tokenize
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceKind, EvidenceRecord, PainPoint
from packages.contracts.gaps import (
    CompetitorProfile,
    CompetitorStatus,
    GapFinding,
    GapKind,
)
from packages.contracts.opportunities import LabeledClaim

_COMPLAINT_CUES = re.compile(
    r"\b(hate|frustrated|annoying|broken|impossible|can't find|cannot find|"
    r"too expensive|doesn't work|does not work|fails|wish there was|struggle|"
    r"problem with|issue with|missing|lacks?|no good)\b",
    re.I,
)


def attach_feedback_to_competitors(
    competitors: list[CompetitorProfile],
    evidence: list[EvidenceRecord],
) -> list[CompetitorProfile]:
    """Link discussion evidence that mentions a competitor; mark weakness only with cues."""
    discussions = [
        e for e in evidence if e.kind is EvidenceKind.DISCUSSION and e.id is not None
    ]
    updated: list[CompetitorProfile] = []
    for competitor in competitors:
        name_key = normalize_text(competitor.name)
        host_key = ""
        if competitor.url:
            host_key = normalize_text(competitor.url)
        feedback_ids = []
        weakness_claims: list[LabeledClaim] = []

        for record in discussions:
            blob = normalize_text(f"{record.title} {record.summary}")
            mentions = bool(name_key and name_key in blob) or bool(
                host_key and host_key in blob
            )
            # Also match first token of competitor name for short brands
            first = name_key.split(" ")[0] if name_key else ""
            if first and len(first) >= 4 and first in blob:
                mentions = True
            if not mentions:
                continue
            feedback_ids.append(record.id)
            text_blob = f"{record.title}. {record.summary}"
            if _COMPLAINT_CUES.search(text_blob):
                weakness_claims.append(
                    LabeledClaim(
                        text=(
                            f"User feedback mentions '{competitor.name}' with complaint cues: "
                            f"{record.title[:120]}"
                        ),
                        claim_tag=ClaimTag.AI_INTERPRETATION,
                        evidence_ids=[record.id],
                    )
                )

        status = CompetitorStatus.OBSERVED_IN_SEARCH
        claims = list(competitor.claims)
        if feedback_ids and weakness_claims:
            status = CompetitorStatus.WEAKNESS_EVIDENCED
        elif feedback_ids:
            status = CompetitorStatus.MENTIONED_IN_FEEDBACK
            claims.append(
                LabeledClaim(
                    text=(
                        f"Mentioned in discussion evidence without complaint cues "
                        f"({len(feedback_ids)} item(s)). Not labeled weak."
                    ),
                    claim_tag=ClaimTag.UNVERIFIED_CLAIM,
                    evidence_ids=list(feedback_ids),
                )
            )
        else:
            status = CompetitorStatus.NO_WEAKNESS_EVIDENCE
            claims.append(
                LabeledClaim(
                    text=(
                        f"No discussion evidence found that supports calling "
                        f"'{competitor.name}' weak."
                    ),
                    claim_tag=ClaimTag.AI_INTERPRETATION,
                    evidence_ids=[],
                )
            )

        updated.append(
            competitor.model_copy(
                update={
                    "feedback_evidence_ids": feedback_ids,
                    "status": status,
                    "claims": claims,
                    "weaknesses": weakness_claims,
                    "limitations": list(competitor.limitations)
                    + [
                        "Weakness labels require discussion evidence with complaint cues.",
                    ],
                }
            )
        )
    return updated


def find_missing_feature_gaps(
    *,
    pain_points: list[PainPoint],
    search_evidence: list[EvidenceRecord],
    max_findings: int = 50,
) -> list[GapFinding]:
    """Pain points whose tokens are absent from search snippets → possible gaps."""
    search_tokens: set[str] = set()
    for record in search_evidence:
        search_tokens |= tokenize(record.title, record.summary)

    findings: list[GapFinding] = []
    for pain in pain_points:
        pain_tokens = tokenize(pain.text)
        if not pain_tokens:
            continue
        uncovered = sorted(pain_tokens - search_tokens)
        coverage = 1 - (len(uncovered) / max(len(pain_tokens), 1))
        # Only flag when search coverage of the pain tokens is low
        if coverage > 0.34 and len(uncovered) < 2:
            continue
        evidence_ids = list(pain.evidence_ids)
        findings.append(
            GapFinding(
                id=uuid4(),
                kind=GapKind.MISSING_FEATURE
                if any(
                    t in pain_tokens
                    for t in {"feature", "tool", "integration", "export", "api"}
                )
                else GapKind.MISSING_CONTENT,
                title=f"Possible gap: {pain.text[:100]}",
                summary=(
                    "Pain-point tokens are weakly covered by collected search snippets. "
                    "This is an interpretive gap hypothesis, not proof competitors lack the feature."
                ),
                claims=[
                    LabeledClaim(
                        text=pain.text,
                        claim_tag=ClaimTag.AI_INTERPRETATION,
                        evidence_ids=evidence_ids,
                    ),
                    LabeledClaim(
                        text=(
                            f"Search-snippet token coverage≈{coverage:.2f}; "
                            f"uncovered tokens={uncovered[:8]}"
                        ),
                        claim_tag=ClaimTag.AI_INTERPRETATION,
                        evidence_ids=[e.id for e in search_evidence if e.id][:20],
                    ),
                ],
                evidence_ids=evidence_ids,
                missing_info=[
                    "Product teardown / feature inventory of named competitors",
                    "Measured content gap validation",
                ],
                limitations=[
                    "Gap inferred from lexical overlap between pain points and SERP snippets.",
                    "Does not assert a named competitor is weak.",
                ],
                attributes={
                    "coverage": round(coverage, 3),
                    "uncovered_tokens": uncovered[:12],
                    "pain_frequency": pain.frequency,
                },
            )
        )

    findings.sort(
        key=lambda f: (
            -int(f.attributes.get("pain_frequency") or 0),
            float(f.attributes.get("coverage") or 1),
        )
    )
    return findings[:max_findings]


def competitor_weakness_findings(
    competitors: list[CompetitorProfile],
) -> list[GapFinding]:
    """Emit gap findings only for competitors with evidenced weaknesses."""
    findings: list[GapFinding] = []
    for competitor in competitors:
        if competitor.status is not CompetitorStatus.WEAKNESS_EVIDENCED:
            continue
        if not competitor.weaknesses:
            continue
        evidence_ids = list(
            dict.fromkeys(
                [
                    *competitor.feedback_evidence_ids,
                    *[eid for claim in competitor.weaknesses for eid in claim.evidence_ids],
                ]
            )
        )
        findings.append(
            GapFinding(
                id=uuid4(),
                kind=GapKind.COMPETITOR_WEAKNESS,
                title=f"Evidenced weakness signal: {competitor.name}",
                summary=(
                    f"{len(competitor.weaknesses)} discussion claim(s) with complaint cues "
                    f"reference '{competitor.name}'. Still not a measured quality score."
                ),
                claims=list(competitor.weaknesses),
                evidence_ids=evidence_ids,
                competitor_name=competitor.name,
                missing_info=[
                    "Independent product verification",
                    "Severity / frequency outside this collection",
                ],
                limitations=[
                    "Only emitted because discussion evidence contained complaint cues.",
                    "Mock discussion text may be synthetic when providers are mocked.",
                ],
                attributes={"status": competitor.status.value},
            )
        )
    return findings


def search_vs_feedback_summary(
    *,
    search_count: int,
    discussion_count: int,
    competitors: list[CompetitorProfile],
    gap_count: int,
) -> tuple[str, list[LabeledClaim]]:
    evidenced = sum(
        1 for c in competitors if c.status is CompetitorStatus.WEAKNESS_EVIDENCED
    )
    text = (
        f"Collected search evidence={search_count}, discussion evidence={discussion_count}. "
        f"Competitors observed={len(competitors)}; with evidenced weakness signals={evidenced}; "
        f"gap findings={gap_count}. "
        "Competitors without complaint-backed evidence are not labeled weak."
    )
    claims = [
        LabeledClaim(
            text=text,
            claim_tag=ClaimTag.AI_INTERPRETATION,
            evidence_ids=[],
        )
    ]
    return text, claims
