"""Emerging theme detection across evidence (lexical, not demand estimates)."""

from __future__ import annotations

from collections import defaultdict

from opportunity_engine.tokens import tokenize
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceRecord
from packages.contracts.opportunities import EmergingTheme
from packages.contracts.providers import ProviderName


def detect_emerging_themes(
    evidence: list[EvidenceRecord],
    *,
    min_evidence: int = 2,
    min_providers: int = 2,
) -> list[EmergingTheme]:
    """Tokens appearing across multiple providers are emerging themes candidates."""
    token_evidence: dict[str, set] = defaultdict(set)
    token_providers: dict[str, set[ProviderName]] = defaultdict(set)

    for record in evidence:
        if record.id is None:
            continue
        tokens = tokenize(record.title, record.summary, record.provenance.query or "")
        for token in tokens:
            token_evidence[token].add(record.id)
            token_providers[token].add(record.provenance.provider)

    themes: list[EmergingTheme] = []
    for token, evidence_ids in token_evidence.items():
        providers = token_providers[token]
        if len(evidence_ids) < min_evidence or len(providers) < min_providers:
            continue
        themes.append(
            EmergingTheme(
                theme=f"Theme around '{token}'",
                token=token,
                evidence_count=len(evidence_ids),
                provider_count=len(providers),
                providers=sorted(providers, key=lambda p: p.value),
                evidence_ids=sorted(evidence_ids, key=str),
                claim_tag=ClaimTag.AI_INTERPRETATION,
                limitations=[
                    "Theme detection is lexical co-occurrence (AI_INTERPRETATION).",
                    "Does not imply search volume, spend, or willingness to pay.",
                    "No fabricated demand metrics are attached.",
                ],
            )
        )

    themes.sort(key=lambda t: (-t.provider_count, -t.evidence_count, t.token))
    return themes
