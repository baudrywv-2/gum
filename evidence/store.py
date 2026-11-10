"""Persist evidence and pain points with fingerprint-based deduplication."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    EvidenceCollection,
    EvidenceRecordRow,
    PainPointRow,
)
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import (
    EvidenceKind,
    EvidenceRecord,
    PainPoint,
    Provenance,
    ReliabilityLevel,
)
from packages.contracts.providers import ProviderMode, ProviderName
from evidence.dedupe import pain_point_key


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_collection(
        self,
        *,
        query: str,
        geography: str | None = None,
        language: str | None = None,
    ) -> EvidenceCollection:
        row = EvidenceCollection(
            id=uuid.uuid4(),
            query=query,
            geography=geography,
            language=language,
            status="completed",
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def add_evidence(self, record: EvidenceRecord) -> tuple[EvidenceRecord, bool]:
        """Insert evidence or return existing duplicate. Returns (record, created)."""
        existing = self.session.scalar(
            select(EvidenceRecordRow).where(
                EvidenceRecordRow.fingerprint == record.fingerprint
            )
        )
        if existing is not None:
            mapped = self._to_evidence(existing)
            mapped.is_duplicate = True
            return mapped, False

        row = EvidenceRecordRow(
            id=record.id or uuid.uuid4(),
            collection_id=record.collection_id,
            kind=record.kind.value,
            title=record.title,
            summary=record.summary,
            fingerprint=record.fingerprint,
            provider=record.provenance.provider.value,
            provider_mode=record.provenance.provider_mode.value,
            source_url=record.provenance.source_url,
            query=record.provenance.query,
            geography=record.provenance.geography,
            language=record.provenance.language,
            claim_tag=record.provenance.claim_tag.value,
            reliability=record.provenance.reliability.value,
            limitations=record.provenance.limitations,
            attributes=record.attributes,
            raw=record.provenance.raw,
            collected_at=record.provenance.collected_at,
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return self._to_evidence(row), True

    def upsert_pain_point(self, pain: PainPoint) -> tuple[PainPoint, bool]:
        """Insert or bump frequency for a normalized pain point."""
        key = pain.normalized_text or pain_point_key(pain.text)
        existing = self.session.scalar(
            select(PainPointRow).where(PainPointRow.normalized_text == key)
        )
        if existing is not None:
            existing.frequency = int(existing.frequency) + int(pain.frequency)
            merged_ids = list(
                dict.fromkeys([*(existing.evidence_ids or []), *[str(i) for i in pain.evidence_ids]])
            )
            existing.evidence_ids = merged_ids
            providers = set(existing.source_providers or [])
            providers.update(p.value for p in pain.source_providers)
            existing.source_providers = sorted(providers)
            if pain.collection_id is not None:
                existing.collection_id = pain.collection_id
            self.session.flush()
            return self._to_pain(existing), False

        row = PainPointRow(
            id=pain.id or uuid.uuid4(),
            collection_id=pain.collection_id,
            text=pain.text,
            normalized_text=key,
            frequency=pain.frequency,
            claim_tag=pain.claim_tag.value,
            evidence_ids=[str(i) for i in pain.evidence_ids],
            source_providers=[p.value for p in pain.source_providers],
            limitations=pain.limitations,
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return self._to_pain(row), True

    def list_evidence(
        self,
        *,
        collection_id: uuid.UUID | None = None,
        kind: EvidenceKind | None = None,
        limit: int = 100,
    ) -> list[EvidenceRecord]:
        stmt = select(EvidenceRecordRow).order_by(EvidenceRecordRow.created_at.desc())
        if collection_id is not None:
            stmt = stmt.where(EvidenceRecordRow.collection_id == collection_id)
        if kind is not None:
            stmt = stmt.where(EvidenceRecordRow.kind == kind.value)
        stmt = stmt.limit(limit)
        return [self._to_evidence(row) for row in self.session.scalars(stmt)]

    def list_pain_points(
        self,
        *,
        collection_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[PainPoint]:
        stmt = select(PainPointRow).order_by(PainPointRow.frequency.desc())
        if collection_id is not None:
            stmt = stmt.where(PainPointRow.collection_id == collection_id)
        stmt = stmt.limit(limit)
        return [self._to_pain(row) for row in self.session.scalars(stmt)]

    def get_collection(self, collection_id: uuid.UUID) -> EvidenceCollection | None:
        return self.session.get(EvidenceCollection, collection_id)

    @staticmethod
    def _to_evidence(row: EvidenceRecordRow) -> EvidenceRecord:
        return EvidenceRecord(
            id=row.id,
            collection_id=row.collection_id,
            kind=EvidenceKind(row.kind),
            title=row.title,
            summary=row.summary,
            fingerprint=row.fingerprint,
            provenance=Provenance(
                provider=ProviderName(row.provider),
                provider_mode=ProviderMode(row.provider_mode),
                source_url=row.source_url,
                query=row.query,
                geography=row.geography,
                language=row.language,
                collected_at=row.collected_at,
                claim_tag=ClaimTag(row.claim_tag),
                reliability=ReliabilityLevel(row.reliability),
                limitations=list(row.limitations or []),
                raw=dict(row.raw or {}),
            ),
            attributes=dict(row.attributes or {}),
            created_at=row.created_at,
            is_duplicate=False,
        )

    @staticmethod
    def _to_pain(row: PainPointRow) -> PainPoint:
        evidence_ids: list[uuid.UUID] = []
        for value in row.evidence_ids or []:
            try:
                evidence_ids.append(uuid.UUID(str(value)))
            except ValueError:
                continue
        return PainPoint(
            id=row.id,
            collection_id=row.collection_id,
            text=row.text,
            normalized_text=row.normalized_text,
            frequency=row.frequency,
            claim_tag=ClaimTag(row.claim_tag),
            evidence_ids=evidence_ids,
            source_providers=[ProviderName(p) for p in (row.source_providers or [])],
            limitations=list(row.limitations or []),
            created_at=row.created_at,
        )
