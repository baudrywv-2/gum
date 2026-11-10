"""Tokenization helpers for clustering and theme detection."""

from __future__ import annotations

import re

from evidence.dedupe import normalize_text

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "for",
        "to",
        "of",
        "in",
        "on",
        "with",
        "is",
        "are",
        "was",
        "were",
        "be",
        "this",
        "that",
        "it",
        "as",
        "at",
        "by",
        "from",
        "mock",
        "serp",
        "google",
        "ads",
        "trends",
        "x",
        "api",
        "result",
        "about",
        "guide",
        "related",
        "signal",
        "insight",
        "synthetic",
        "placeholder",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def tokenize(*parts: str) -> set[str]:
    blob = normalize_text(" ".join(p for p in parts if p))
    tokens = set(_TOKEN_RE.findall(blob))
    return {t for t in tokens if t not in _STOPWORDS}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0
