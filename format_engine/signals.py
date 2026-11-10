"""Evidence signals for format fit — interpretive, never fabricated demand."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from evidence.dedupe import normalize_text
from opportunity_engine.tokens import tokenize
from packages.contracts.evidence import EvidenceKind, EvidenceRecord, PainPoint
from packages.contracts.gaps import CompetitorStatus, GapFinding, GapKind, GapReport


@dataclass
class FormatSignals:
    query: str
    search_count: int = 0
    discussion_count: int = 0
    pain_point_count: int = 0
    gap_finding_count: int = 0
    evidenced_competitor_weaknesses: int = 0
    evidence_ids: list[UUID] = field(default_factory=list)
    pain_evidence_ids: list[UUID] = field(default_factory=list)
    tokens: set[str] = field(default_factory=set)
    flags: set[str] = field(default_factory=set)

    @property
    def discussion_heavy(self) -> bool:
        return self.discussion_count >= max(1, self.search_count)

    @property
    def search_heavy(self) -> bool:
        return self.search_count > self.discussion_count


_TOOL_TOKENS = {
    "calculator",
    "tool",
    "estimate",
    "converter",
    "generator",
    "template",
    "csv",
    "export",
    "automation",
}
_CONTENT_TOKENS = {
    "guide",
    "how",
    "tutorial",
    "learn",
    "explain",
    "blog",
    "article",
    "tips",
}
_VIDEO_TOKENS = {"youtube", "video", "watch", "demo", "tutorial"}
_DIRECTORY_TOKENS = {"directory", "list", "compare", "comparison", "alternatives", "best"}
_MARKETPLACE_TOKENS = {"marketplace", "freelance", "hire", "sellers", "buyers"}
_SAAS_TOKENS = {"saas", "subscription", "dashboard", "account", "login", "billing"}
_API_TOKENS = {"api", "webhook", "integration", "data", "endpoint"}
_MOBILE_TOKENS = {"android", "ios", "iphone", "mobile", "app store", "play store"}
_NEWSLETTER_TOKENS = {"newsletter", "alert", "digest", "subscribe", "email"}
_AGENT_TOKENS = {"agent", "automate", "automation", "bot", "workflow"}
_SERVICES_TOKENS = {"consulting", "agency", "freelancer", "done", "service"}


def build_signals(
    *,
    query: str,
    evidence: list[EvidenceRecord],
    pain_points: list[PainPoint],
    gap_report: GapReport | None = None,
) -> FormatSignals:
    search = [e for e in evidence if e.kind is EvidenceKind.SEARCH]
    discussion = [e for e in evidence if e.kind is EvidenceKind.DISCUSSION]
    evidence_ids = [e.id for e in evidence if e.id is not None]
    pain_ids = [i for p in pain_points for i in p.evidence_ids]

    tokens: set[str] = tokenize(query)
    for record in evidence:
        tokens |= tokenize(record.title, record.summary)
    for pain in pain_points:
        tokens |= tokenize(pain.text)

    flags: set[str] = set()
    if tokens & _TOOL_TOKENS:
        flags.add("toolish")
    if tokens & _CONTENT_TOKENS:
        flags.add("contentish")
    if tokens & _VIDEO_TOKENS:
        flags.add("videoish")
    if tokens & _DIRECTORY_TOKENS:
        flags.add("directoryish")
    if tokens & _MARKETPLACE_TOKENS:
        flags.add("marketplaceish")
    if tokens & _SAAS_TOKENS:
        flags.add("saasish")
    if tokens & _API_TOKENS:
        flags.add("apiish")
    if tokens & _MOBILE_TOKENS or "mobile" in normalize_text(query):
        flags.add("mobileish")
    if tokens & _NEWSLETTER_TOKENS:
        flags.add("newsletterish")
    if tokens & _AGENT_TOKENS:
        flags.add("agentish")
    if tokens & _SERVICES_TOKENS:
        flags.add("servicesish")
    if any("missing" in normalize_text(p.text) or "wish" in normalize_text(p.text) for p in pain_points):
        flags.add("unmet_need")

    evidenced_weak = 0
    gap_count = 0
    if gap_report is not None:
        gap_count = len(gap_report.findings)
        evidenced_weak = sum(
            1
            for c in gap_report.competitors
            if c.status is CompetitorStatus.WEAKNESS_EVIDENCED
        )
        for finding in gap_report.findings:
            if finding.kind in {GapKind.MISSING_FEATURE, GapKind.MISSING_CONTENT}:
                flags.add("gap_signal")
            if finding.kind is GapKind.MISSING_FEATURE:
                flags.add("toolish")
            if finding.kind is GapKind.MISSING_CONTENT:
                flags.add("contentish")

    return FormatSignals(
        query=query,
        search_count=len(search),
        discussion_count=len(discussion),
        pain_point_count=len(pain_points),
        gap_finding_count=gap_count,
        evidenced_competitor_weaknesses=evidenced_weak,
        evidence_ids=evidence_ids,
        pain_evidence_ids=list(dict.fromkeys(pain_ids)),
        tokens=tokens,
        flags=flags,
    )
