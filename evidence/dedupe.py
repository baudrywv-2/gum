"""Evidence fingerprinting and text normalization for deduplication."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from packages.contracts.evidence import EvidenceKind
from packages.contracts.providers import ProviderName

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]+")


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.casefold().strip()
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def evidence_fingerprint(
    *,
    kind: EvidenceKind,
    provider: ProviderName,
    title: str,
    summary: str,
    source_url: str | None = None,
) -> str:
    """Stable hash used to deduplicate identical observations."""
    url_part = normalize_text(source_url or "")
    payload = "|".join(
        [
            kind.value,
            provider.value,
            url_part or normalize_text(title),
            normalize_text(summary)[:500],
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def pain_point_key(text: str) -> str:
    return normalize_text(text)
