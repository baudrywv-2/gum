"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ClaimTagBadge } from "@/components/ClaimTag";
import { ScoreBar } from "@/components/ScoreBar";
import { getReport, type OpportunityReport } from "@/lib/api";

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<OpportunityReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getReport(params.id)
      .then((payload) => {
        if (!cancelled) setReport(payload);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load report");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  if (error) {
    return <main className="text-warn">{error}</main>;
  }
  if (!report) {
    return <main className="text-muted">Loading report…</main>;
  }

  const scores = [
    ["Demand evidence", report.scores.demand_evidence],
    ["Organic ranking feasibility", report.scores.organic_ranking_feasibility],
    ["Format fit", report.scores.format_fit],
    ["Business viability", report.scores.business_viability],
    ["Evidence confidence", report.scores.evidence_confidence],
    ["Overall priority", report.scores.overall_priority],
  ] as const;

  return (
    <main>
      <p className="page-kicker">Opportunity report</p>
      <h2 className="page-title">{report.title}</h2>
      <p className="page-lede">{report.summary}</p>

      <dl className="section-rule grid gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted">Problem</dt>
          <dd className="mt-1 text-ink-soft">{report.problem}</dd>
        </div>
        <div>
          <dt className="text-muted">Audience</dt>
          <dd className="mt-1 text-ink-soft">{report.audience ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-muted">Format</dt>
          <dd className="mt-1 text-ink-soft">
            {report.recommended_format ?? "—"}
          </dd>
        </div>
      </dl>

      <section className="mt-10 space-y-5">
        <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-muted">
          Scores
        </h3>
        {scores.map(([label, block]) => (
          <ScoreBar
            key={label}
            label={label}
            score={block.score}
            explanation={block.explanation}
          />
        ))}
      </section>

      <section className="section-rule">
        <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-muted">
          Unmet needs
        </h3>
        <ul className="mt-3 space-y-2">
          {report.unmet_needs.map((need) => (
            <li key={need.text} className="flex flex-wrap items-center gap-2 text-sm">
              <ClaimTagBadge tag={need.claim_tag} />
              <span className="text-ink-soft">{need.text}</span>
            </li>
          ))}
          {report.unmet_needs.length === 0 && (
            <li className="text-muted">None extracted.</li>
          )}
        </ul>
      </section>

      <section className="section-rule">
        <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-muted">
          Next actions
        </h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-ink-soft">
          {report.next_actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-muted">
          Cheapest validation: {report.cheapest_validation_experiment ?? "—"}
        </p>
      </section>

      <section className="section-rule">
        <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-muted">
          Missing info & limitations
        </h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
          {[...report.missing_info, ...report.limitations].slice(0, 10).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
