"""Persist gap reports, competitors, and findings."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import CompetitorRow, GapFindingRow, GapReportRow
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.gaps import (
    CompetitorProfile,
    CompetitorStatus,
    GapFinding,
    GapKind,
    GapReport,
)
from packages.contracts.opportunities import LabeledClaim
from packages.contracts.providers import ProviderName


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_claims(raw_claims: list) -> list[LabeledClaim]:
    claims: list[LabeledClaim] = []
    for raw in raw_claims or []:
        try:
            evidence_ids = []
            for eid in raw.get("evidence_ids") or []:
                try:
                    evidence_ids.append(uuid.UUID(str(eid)))
                except ValueError:
                    continue
            claims.append(
                LabeledClaim(
                    text=raw["text"],
                    claim_tag=ClaimTag(raw["claim_tag"]),
                    evidence_ids=evidence_ids,
                )
            )
        except (KeyError, ValueError):
            continue
    return claims


def _parse_uuids(values: list) -> list[uuid.UUID]:
    out: list[uuid.UUID] = []
    for value in values or []:
        try:
            out.append(uuid.UUID(str(value)))
        except ValueError:
            continue
    return out


class GapStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_report(self, report: GapReport) -> GapReport:
        report_id = report.id or uuid.uuid4()
        row = GapReportRow(
            id=report_id,
            collection_id=report.collection_id,
            query=report.query,
            geography=report.geography,
            language=report.language,
            search_vs_feedback=report.search_vs_feedback,
            claims=[c.model_dump(mode="json") for c in report.claims],
            missing_info=list(report.missing_info),
            limitations=list(report.limitations),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()

        competitors: list[CompetitorProfile] = []
        for competitor in report.competitors:
            competitors.append(self._save_competitor(report_id, competitor))

        findings: list[GapFinding] = []
        for finding in report.findings:
            findings.append(self._save_finding(report_id, finding))

        return report.model_copy(
            update={
                "id": report_id,
                "competitors": competitors,
                "findings": findings,
                "created_at": row.created_at,
            }
        )

    def _save_competitor(
        self, report_id: uuid.UUID, competitor: CompetitorProfile
    ) -> CompetitorProfile:
        row = CompetitorRow(
            id=competitor.id or uuid.uuid4(),
            report_id=report_id,
            name=competitor.name,
            url=competitor.url,
            source_providers=[p.value for p in competitor.source_providers],
            search_evidence_ids=[str(i) for i in competitor.search_evidence_ids],
            feedback_evidence_ids=[str(i) for i in competitor.feedback_evidence_ids],
            status=competitor.status.value,
            claims=[c.model_dump(mode="json") for c in competitor.claims],
            weaknesses=[c.model_dump(mode="json") for c in competitor.weaknesses],
            limitations=list(competitor.limitations),
            attributes=dict(competitor.attributes),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return competitor.model_copy(update={"id": row.id})

    def _save_finding(
        self, report_id: uuid.UUID, finding: GapFinding
    ) -> GapFinding:
        row = GapFindingRow(
            id=finding.id or uuid.uuid4(),
            report_id=report_id,
            kind=finding.kind.value,
            title=finding.title,
            summary=finding.summary,
            claims=[c.model_dump(mode="json") for c in finding.claims],
            evidence_ids=[str(i) for i in finding.evidence_ids],
            competitor_name=finding.competitor_name,
            missing_info=list(finding.missing_info),
            limitations=list(finding.limitations),
            attributes=dict(finding.attributes),
            created_at=_utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return finding.model_copy(update={"id": row.id})

    def get_report(self, report_id: uuid.UUID) -> GapReport | None:
        row = self.session.get(GapReportRow, report_id)
        if row is None:
            return None
        competitors = [
            self._to_competitor(c)
            for c in self.session.scalars(
                select(CompetitorRow).where(CompetitorRow.report_id == report_id)
            )
        ]
        findings = [
            self._to_finding(f)
            for f in self.session.scalars(
                select(GapFindingRow).where(GapFindingRow.report_id == report_id)
            )
        ]
        return GapReport(
            id=row.id,
            collection_id=row.collection_id,
            query=row.query,
            geography=row.geography,
            language=row.language,
            competitors=competitors,
            findings=findings,
            search_vs_feedback=row.search_vs_feedback,
            claims=_parse_claims(row.claims),
            missing_info=list(row.missing_info or []),
            limitations=list(row.limitations or []),
            created_at=row.created_at,
        )

    def list_reports(self, *, limit: int = 50) -> list[GapReport]:
        rows = self.session.scalars(
            select(GapReportRow).order_by(GapReportRow.created_at.desc()).limit(limit)
        )
        return [self.get_report(row.id) for row in rows if row.id]

    @staticmethod
    def _to_competitor(row: CompetitorRow) -> CompetitorProfile:
        providers = []
        for p in row.source_providers or []:
            try:
                providers.append(ProviderName(p))
            except ValueError:
                continue
        return CompetitorProfile(
            id=row.id,
            name=row.name,
            url=row.url,
            source_providers=providers,
            search_evidence_ids=_parse_uuids(row.search_evidence_ids),
            feedback_evidence_ids=_parse_uuids(row.feedback_evidence_ids),
            status=CompetitorStatus(row.status),
            claims=_parse_claims(row.claims),
            weaknesses=_parse_claims(row.weaknesses),
            limitations=list(row.limitations or []),
            attributes=dict(row.attributes or {}),
        )

    @staticmethod
    def _to_finding(row: GapFindingRow) -> GapFinding:
        return GapFinding(
            id=row.id,
            kind=GapKind(row.kind),
            title=row.title,
            summary=row.summary,
            claims=_parse_claims(row.claims),
            evidence_ids=_parse_uuids(row.evidence_ids),
            competitor_name=row.competitor_name,
            missing_info=list(row.missing_info or []),
            limitations=list(row.limitations or []),
            attributes=dict(row.attributes or {}),
        )
