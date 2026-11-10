"""Orchestrate mock-provider collection into persisted evidence + pain points."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from evidence.dedupe import evidence_fingerprint
from evidence.pain_points import extract_pain_points
from evidence.store import EvidenceStore
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import (
    CollectEvidenceRequest,
    CollectEvidenceResult,
    EvidenceKind,
    EvidenceRecord,
    Provenance,
    ReliabilityLevel,
)
from packages.contracts.providers import (
    ProviderMode,
    ProviderName,
    ProviderRequest,
    ProviderResponse,
    ProviderResultItem,
)
from providers.registry import ProviderRegistry, get_registry


class EvidenceCollector:
    """Collect search + discussion evidence via provider registry (mock-safe)."""

    def __init__(
        self,
        session: Session,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.store = EvidenceStore(session)
        self.registry = registry or get_registry()
        self.session = session

    def collect(self, request: CollectEvidenceRequest) -> CollectEvidenceResult:
        collection = self.store.create_collection(
            query=request.query,
            geography=request.geography,
            language=request.language,
        )

        created = 0
        deduped = 0
        stored: list[EvidenceRecord] = []
        limitations = [
            "Milestone 3 uses mock/stub providers unless live clients are explicitly enabled.",
            "Do not treat mocked volumes or social posts as measured demand.",
        ]

        if request.include_search:
            for provider_name in request.providers_search:
                response = self._safe_search(provider_name, request)
                if response is None:
                    limitations.append(f"Search provider unavailable: {provider_name.value}")
                    continue
                for item in response.items[: request.limit_per_provider]:
                    record = self._item_to_record(
                        kind=EvidenceKind.SEARCH,
                        collection_id=collection.id,
                        response=response,
                        item=item,
                        request=request,
                    )
                    saved, was_created = self.store.add_evidence(record)
                    stored.append(saved)
                    if was_created:
                        created += 1
                    else:
                        deduped += 1
                limitations.extend(response.limitations)

        discussion_records: list[EvidenceRecord] = []
        discussion_unavailable = False
        if request.include_discussions:
            for provider_name in request.providers_discussion:
                response = self._safe_search(provider_name, request)
                if response is None:
                    discussion_unavailable = True
                    limitations.append(
                        f"Discussion provider unavailable: {provider_name.value}"
                    )
                    continue
                limitations.extend(response.limitations)
                if response.mode is ProviderMode.UNAVAILABLE:
                    discussion_unavailable = True
                    limitations.append(
                        f"Discussion provider {provider_name.value} returned "
                        f"unavailable ({(response.raw or {}).get('error') or 'error'}); "
                        "no synthetic discussion substituted."
                    )
                    continue
                if (
                    response.mode is ProviderMode.MOCK
                    and provider_name is not ProviderName.MOCK
                ):
                    # Force-mock / stub path for a live-named provider — keep items but
                    # mark that discussion is not live.
                    limitations.append(
                        f"Discussion provider {provider_name.value} ran in MOCK mode; "
                        "treat discussion claims as UNVERIFIED / HYPOTHESIS only."
                    )
                for item in response.items[: request.limit_per_provider]:
                    record = self._item_to_record(
                        kind=EvidenceKind.DISCUSSION,
                        collection_id=collection.id,
                        response=response,
                        item=item,
                        request=request,
                    )
                    saved, was_created = self.store.add_evidence(record)
                    stored.append(saved)
                    discussion_records.append(saved)
                    if was_created:
                        created += 1
                    else:
                        deduped += 1

        pain_created = 0
        pain_updated = 0
        pain_points = []
        if request.extract_pain_points:
            live_discussion = [
                r
                for r in discussion_records
                if r.provenance.provider_mode is not ProviderMode.MOCK
            ]
            mock_discussion = [
                r
                for r in discussion_records
                if r.provenance.provider_mode is ProviderMode.MOCK
            ]
            if live_discussion:
                source = live_discussion
            elif mock_discussion:
                # Explicit MOCK discussion only — still extract, but callers demote cards.
                source = mock_discussion
                limitations.append(
                    "Pain points derived from MOCK discussion only — not live user voice."
                )
            elif discussion_unavailable or request.include_discussions:
                # X (or other discussion) down with nothing stored: do not invent pains
                # from mock, and do not scrape SERP titles into "recurring problems".
                source = []
                limitations.append(
                    "Live discussion unavailable; pain-point extraction skipped "
                    "(no synthetic discussion). Opportunity cards should prefer "
                    "SerpAPI/YouTube MEASURED_FACT themes instead."
                )
            else:
                source = []

            extracted = extract_pain_points(source, collection_id=collection.id)
            for pain in extracted:
                saved, was_created = self.store.upsert_pain_point(pain)
                pain_points.append(saved)
                if was_created:
                    pain_created += 1
                else:
                    pain_updated += 1

        self.session.commit()

        # Deduplicate limitation strings while preserving order.
        unique_limitations = list(dict.fromkeys(limitations))

        # Return all evidence visible on this collection (new + linked duplicates).
        # Deduped rows remain labeled via is_duplicate for transparency.
        visible = self.store.list_evidence(collection_id=collection.id, limit=500)
        by_id = {r.id: r for r in stored if r.id is not None}
        for item in visible:
            prior = by_id.get(item.id)
            if prior is not None and prior.is_duplicate:
                item.is_duplicate = True

        return CollectEvidenceResult(
            collection_id=collection.id,
            query=request.query,
            evidence_created=created,
            evidence_deduplicated=deduped,
            pain_points_created=pain_created,
            pain_points_updated=pain_updated,
            evidence=visible,
            pain_points=pain_points,
            limitations=unique_limitations,
        )

    def _safe_search(
        self, provider_name: ProviderName, request: CollectEvidenceRequest
    ) -> ProviderResponse | None:
        try:
            return self.registry.search(
                provider_name,
                ProviderRequest(
                    query=request.query,
                    geography=request.geography,
                    language=request.language,
                    limit=request.limit_per_provider,
                ),
            )
        except KeyError:
            return None

    @staticmethod
    def _item_to_record(
        *,
        kind: EvidenceKind,
        collection_id,
        response: ProviderResponse,
        item: ProviderResultItem,
        request: CollectEvidenceRequest,
    ) -> EvidenceRecord:
        title = item.title
        summary = item.snippet or response.summary
        fingerprint = evidence_fingerprint(
            kind=kind,
            provider=response.provider,
            title=title,
            summary=summary or "",
            source_url=item.url,
        )
        reliability = (
            ReliabilityLevel.LOW
            if response.mode is ProviderMode.MOCK
            else ReliabilityLevel.MEDIUM
        )
        claim_tag = item.claim_tag or ClaimTag.UNVERIFIED_CLAIM
        return EvidenceRecord(
            collection_id=collection_id,
            kind=kind,
            title=title,
            summary=summary or title,
            fingerprint=fingerprint,
            provenance=Provenance(
                provider=response.provider,
                provider_mode=response.mode,
                source_url=item.url,
                query=request.query,
                geography=request.geography,
                language=request.language,
                collected_at=response.fetched_at or datetime.now(timezone.utc),
                claim_tag=claim_tag,
                reliability=reliability,
                limitations=list(response.limitations),
                raw={
                    "provider_raw": response.raw,
                    "item_attributes": item.attributes,
                    "cached": response.cached,
                },
            ),
            attributes={
                "snippet": item.snippet,
                "score": item.score,
                "item_attributes": item.attributes,
                "kind": kind.value,
            },
        )
