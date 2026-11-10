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
    return <main className="text-amber-300">{error}</main>;
  }
  if (!report) {
    return <main className="text-zinc-400">Loading report…</main>;
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
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Opportunity report
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        {report.title}
      </h2>
      <p className="mt-3 max-w-3xl text-zinc-300">{report.summary}</p>

      <dl className="mt-8 grid gap-4 border-t border-white/10 pt-6 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-zinc-500">Problem</dt>
          <dd className="mt-1 text-zinc-200">{report.problem}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Audience</dt>
          <dd className="mt-1 text-zinc-200">{report.audience ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Format</dt>
          <dd className="mt-1 text-zinc-200">
            {report.recommended_format ?? "—"}
          </dd>
        </div>
      </dl>

      <section className="mt-10 space-y-5">
        <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
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

      <section className="mt-10 border-t border-white/10 pt-6">
        <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
          Unmet needs
        </h3>
        <ul className="mt-3 space-y-2">
          {report.unmet_needs.map((need) => (
            <li key={need.text} className="flex flex-wrap items-center gap-2 text-sm">
              <ClaimTagBadge tag={need.claim_tag} />
              <span className="text-zinc-300">{need.text}</span>
            </li>
          ))}
          {report.unmet_needs.length === 0 && (
            <li className="text-zinc-500">None extracted.</li>
          )}
        </ul>
      </section>

      <section className="mt-10 border-t border-white/10 pt-6">
        <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
          Next actions
        </h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-zinc-300">
          {report.next_actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-zinc-400">
          Cheapest validation: {report.cheapest_validation_experiment ?? "—"}
        </p>
      </section>

      <section className="mt-10 border-t border-white/10 pt-6">
        <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
          Missing info & limitations
        </h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-zinc-500">
          {[...report.missing_info, ...report.limitations].slice(0, 10).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
