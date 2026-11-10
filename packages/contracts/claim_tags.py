"""Evidence claim tagging vocabulary (non-negotiable product rule)."""

from __future__ import annotations

from enum import Enum


class ClaimTag(str, Enum):
    MEASURED_FACT = "MEASURED_FACT"
    PROVIDER_ESTIMATE = "PROVIDER_ESTIMATE"
    AI_INTERPRETATION = "AI_INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    UNVERIFIED_CLAIM = "UNVERIFIED_CLAIM"
