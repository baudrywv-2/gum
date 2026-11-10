"""Shared GUM contracts (Pydantic models used across services)."""

from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import (
    CollectEvidenceRequest,
    CollectEvidenceResult,
    EvidenceKind,
    EvidenceRecord,
    PainPoint,
    Provenance,
    ReliabilityLevel,
)
from packages.contracts.health import HealthStatus
from packages.contracts.opportunities import (
    CrossSourceCorrelation,
    DiscoverOpportunitiesRequest,
    DiscoverOpportunitiesResult,
    EmergingTheme,
    EvidenceCluster,
    LabeledClaim,
    Opportunity,
    OpportunityType,
    UnderservedAudienceHypothesis,
)
from packages.contracts.providers import (
    MockProviderResult,
    ProviderCapability,
    ProviderMode,
    ProviderName,
    ProviderRequest,
    ProviderResponse,
    ProviderResultItem,
    ProviderStatus,
    ProviderUsageRecord,
)

__all__ = [
    "ClaimTag",
    "CollectEvidenceRequest",
    "CollectEvidenceResult",
    "CrossSourceCorrelation",
    "DiscoverOpportunitiesRequest",
    "DiscoverOpportunitiesResult",
    "EmergingTheme",
    "EvidenceCluster",
    "EvidenceKind",
    "EvidenceRecord",
    "HealthStatus",
    "LabeledClaim",
    "MockProviderResult",
    "Opportunity",
    "OpportunityType",
    "PainPoint",
    "Provenance",
    "ProviderCapability",
    "ProviderMode",
    "ProviderName",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderResultItem",
    "ProviderStatus",
    "ProviderUsageRecord",
    "ReliabilityLevel",
    "UnderservedAudienceHypothesis",
]
