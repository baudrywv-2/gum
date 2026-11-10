"""Extract existing solutions / competitors from search evidence."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from uuid import uuid4

from evidence.dedupe import normalize_text
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceKind, EvidenceRecord
from packages.contracts.gaps import CompetitorProfile, CompetitorStatus
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.providers import ProviderName

_BRAND_RE = re.compile(
    r"(?:\[MOCK serp\]\s*)?(?:Guide:\s*)?([A-Z][A-Za-z0-9][A-Za-z0-9+.&-]{1,40})"
)
_SKIP_HOSTS = {"example.invalid", "example.com", "localhost"}


def _host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _name_from_record(record: EvidenceRecord) -> str | None:
    host = _host(record.provenance.source_url)
    if host and host not in _SKIP_HOSTS:
        label = host.split(".")[0]
        if label and label not in {"www", "search", "guide"}:
            return label

    match = _BRAND_RE.search(record.title)
    if match:
        candidate = match.group(1).strip(" -:|")
        lowered = candidate.casefold()
        if lowered not in {"result", "guide", "mock", "serp", "about"}:
            return candidate

    # Fallback: first meaningful tokens from title
    tokens = normalize_text(record.title).split()
    useful = [t for t in tokens if t not in {"mock", "serp", "guide", "result", "about"}]
    if useful:
        return " ".join(useful[:3])
    return None


def extract_competitors(
    evidence: list[EvidenceRecord],
    *,
    max_competitors: int = 20,
) -> list[CompetitorProfile]:
    """Build competitor profiles from search evidence only (observed, not judged)."""
    search = [e for e in evidence if e.kind is EvidenceKind.SEARCH and e.id is not None]
    buckets: dict[str, CompetitorProfile] = {}

    for record in search:
        name = _name_from_record(record)
        if not name:
            continue
        key = normalize_text(name)
        if not key:
            continue
        if key not in buckets:
            buckets[key] = CompetitorProfile(
                id=uuid4(),
                name=name,
                url=record.provenance.source_url,
                source_providers=[record.provenance.provider],
                search_evidence_ids=[record.id],
                status=CompetitorStatus.OBSERVED_IN_SEARCH,
                claims=[
                    LabeledClaim(
                        text=f"Observed in search evidence as '{name}'",
                        claim_tag=ClaimTag.UNVERIFIED_CLAIM
                        if record.provenance.provider_mode.value == "mock"
                        else ClaimTag.MEASURED_FACT,
                        evidence_ids=[record.id],
                    )
                ],
                weaknesses=[],
                limitations=[
                    "Presence in search results does not imply quality or weakness.",
                    "No competitor weakness is asserted without discussion evidence.",
                ],
                attributes={"titles": [record.title]},
            )
        else:
            profile = buckets[key]
            if record.id not in profile.search_evidence_ids:
                profile.search_evidence_ids.append(record.id)
            if record.provenance.provider not in profile.source_providers:
                profile.source_providers.append(record.provenance.provider)
            titles = list(profile.attributes.get("titles") or [])
            titles.append(record.title)
            profile.attributes["titles"] = titles[:10]
            if not profile.url and record.provenance.source_url:
                profile.url = record.provenance.source_url

    profiles = list(buckets.values())
    profiles.sort(key=lambda p: (-len(p.search_evidence_ids), p.name.casefold()))
    return profiles[:max_competitors]
