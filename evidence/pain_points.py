"""Heuristic pain-point extraction from discussion evidence.

Extractions statements are tagged AI_INTERPRETATION — never MEASURED_FACT.
"""

from __future__ import annotations

import re
from collections import defaultdict
from uuid import UUID

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceRecord, PainPoint
from packages.contracts.providers import ProviderName
from evidence.dedupe import pain_point_key

# Lightweight complaint / unmet-need cues for mock pipeline testing.
_PAIN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(hate|frustrated|annoying|broken|impossible)\b.{0,80}", re.I),
    re.compile(r"\bwish (there was|i could|we had)\b.{0,80}", re.I),
    re.compile(r"\b(can'?t find|cannot find|hard to find|no good)\b.{0,80}", re.I),
    re.compile(r"\b(too expensive|overpriced|waste of (time|money))\b.{0,80}", re.I),
    re.compile(r"\b(pain point|problem with|issue with|struggle with)\b.{0,80}", re.I),
    re.compile(r"\b(doesn'?t work|does not work|fails to)\b.{0,80}", re.I),
]


def _candidate_phrases(text: str) -> list[str]:
    phrases: list[str] = []
    for pattern in _PAIN_PATTERNS:
        for match in pattern.finditer(text):
            phrase = " ".join(match.group(0).split())
            if len(phrase) >= 8:
                phrases.append(phrase[:180])
    return phrases


def extract_pain_points(
    evidence: list[EvidenceRecord],
    *,
    collection_id: UUID | None = None,
) -> list[PainPoint]:
    """Group recurring complaint-like phrases across discussion evidence."""
    buckets: dict[str, dict] = defaultdict(
        lambda: {
            "text": "",
            "count": 0,
            "evidence_ids": [],
            "providers": set(),
        }
    )

    for record in evidence:
        blob = f"{record.title}. {record.summary}"
        attrs_snippet = record.attributes.get("snippet")
        if isinstance(attrs_snippet, str):
            blob = f"{blob} {attrs_snippet}"
        for phrase in _candidate_phrases(blob):
            key = pain_point_key(phrase)
            if not key:
                continue
            bucket = buckets[key]
            if not bucket["text"]:
                bucket["text"] = phrase
            bucket["count"] += 1
            if record.id is not None:
                bucket["evidence_ids"].append(record.id)
            bucket["providers"].add(record.provenance.provider)

    # Also surface title-level mock discussion items as weak candidates when
    # patterns miss (mock providers often lack natural complaint phrasing).
    if not buckets:
        for record in evidence:
            if record.kind.value != "discussion":
                continue
            key = pain_point_key(record.title)
            if not key:
                continue
            bucket = buckets[key]
            bucket["text"] = record.title
            bucket["count"] += 1
            if record.id is not None:
                bucket["evidence_ids"].append(record.id)
            bucket["providers"].add(record.provenance.provider)

    pain_points: list[PainPoint] = []
    for key, bucket in buckets.items():
        providers = sorted(bucket["providers"], key=lambda p: p.value)
        pain_points.append(
            PainPoint(
                collection_id=collection_id,
                text=bucket["text"],
                normalized_text=key,
                frequency=bucket["count"],
                claim_tag=ClaimTag.AI_INTERPRETATION,
                evidence_ids=list(dict.fromkeys(bucket["evidence_ids"])),
                source_providers=providers,
                limitations=[
                    "Pain points are heuristically extracted (AI_INTERPRETATION).",
                    "Not measured survey data or verified user interviews.",
                ],
            )
        )

    pain_points.sort(key=lambda p: (-p.frequency, p.normalized_text))
    return pain_points


def merge_pain_point_frequency(
    existing: PainPoint, incoming: PainPoint
) -> PainPoint:
    evidence_ids = list(dict.fromkeys([*existing.evidence_ids, *incoming.evidence_ids]))
    providers = {
        *(existing.source_providers or []),
        *(incoming.source_providers or []),
    }
    return existing.model_copy(
        update={
            "frequency": existing.frequency + incoming.frequency,
            "evidence_ids": evidence_ids,
            "source_providers": sorted(providers, key=lambda p: p.value),
        }
    )
