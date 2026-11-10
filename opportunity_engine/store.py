"""Persist discovery runs, clusters, and opportunities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import EvidenceClusterRow, OpportunityRow, OpportunityRun
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.opportunities import (
    EvidenceCluster,
    LabeledClaim,
    Opportunity,
    OpportunityType,
)
from packages.contracts.providers import ProviderName


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OpportunityStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        collection_id: uuid.UUID,
        query: str,
        geography: str | None = None,
        language: str | None = None,
    ) -> OpportunityRun:
        row = OpportunityRun(
            id=uuid.uuid4(),
            collection_id=collection_id,
            query=query,
            geography=geography,
            language=language,
            status="completed",
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def save_cluster(self, *, run_id: uuid.UUID, cluster: EvidenceCluster) -> EvidenceCluster:
        row = EvidenceClusterRow(
            id=cluster.id or uuid.uuid4(),
            run_id=run_id,
            label=cluster.label,
            evidence_ids=[str(i) for i in cluster.evidence_ids],
            providers=[p.value for p in cluster.providers],
            kinds=list(cluster.kinds),
            shared_tokens=list(cluster.shared_tokens),
            size=cluster.size,
            claim_tag=cluster.claim_tag.value,
            limitations=list(cluster.limitations),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return cluster.model_copy(update={"id": row.id})

    def save_opportunity(self, opportunity: Opportunity) -> Opportunity:
        row = OpportunityRow(
            id=opportunity.id or uuid.uuid4(),
            run_id=opportunity.run_id,
            collection_id=opportunity.collection_id,
            opportunity_type=opportunity.opportunity_type.value,
            title=opportunity.title,
            summary=opportunity.summary,
            problem=opportunity.problem,
            audience=opportunity.audience,
            geography=opportunity.geography,
            language=opportunity.language,
            claims=[c.model_dump(mode="json") for c in opportunity.claims],
            evidence_ids=[str(i) for i in opportunity.evidence_ids],
            providers=[p.value for p in opportunity.providers],
            themes=list(opportunity.themes),
            missing_info=list(opportunity.missing_info),
            limitations=list(opportunity.limitations),
            attributes=dict(opportunity.attributes),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return self._to_opportunity(row)

    def list_opportunities(
        self,
        *,
        run_id: uuid.UUID | None = None,
        collection_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[Opportunity]:
        stmt = select(OpportunityRow).order_by(OpportunityRow.created_at.desc())
        if run_id is not None:
            stmt = stmt.where(OpportunityRow.run_id == run_id)
        if collection_id is not None:
            stmt = stmt.where(OpportunityRow.collection_id == collection_id)
        stmt = stmt.limit(limit)
        return [self._to_opportunity(row) for row in self.session.scalars(stmt)]

    def get_run(self, run_id: uuid.UUID) -> OpportunityRun | None:
        return self.session.get(OpportunityRun, run_id)

    @staticmethod
    def _to_opportunity(row: OpportunityRow) -> Opportunity:
        evidence_ids: list[uuid.UUID] = []
        for value in row.evidence_ids or []:
            try:
                evidence_ids.append(uuid.UUID(str(value)))
            except ValueError:
                continue
        claims = []
        for raw in row.claims or []:
            try:
                claim_evidence = []
                for eid in raw.get("evidence_ids") or []:
                    try:
                        claim_evidence.append(uuid.UUID(str(eid)))
                    except ValueError:
                        continue
                claims.append(
                    LabeledClaim(
                        text=raw["text"],
                        claim_tag=ClaimTag(raw["claim_tag"]),
                        evidence_ids=claim_evidence,
                    )
                )
            except (KeyError, ValueError):
                continue
        providers = []
        for p in row.providers or []:
            try:
                providers.append(ProviderName(p))
            except ValueError:
                continue
        return Opportunity(
            id=row.id,
            run_id=row.run_id,
            collection_id=row.collection_id,
            opportunity_type=OpportunityType(row.opportunity_type),
            title=row.title,
            summary=row.summary,
            problem=row.problem,
            audience=row.audience,
            geography=row.geography,
            language=row.language,
            claims=claims,
            evidence_ids=evidence_ids,
            providers=providers,
            themes=list(row.themes or []),
            missing_info=list(row.missing_info or []),
            limitations=list(row.limitations or []),
            attributes=dict(row.attributes or {}),
            created_at=row.created_at,
        )
