"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listReports, type OpportunityReport } from "@/lib/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<OpportunityReport[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listReports()
      .then((payload) => {
        if (!cancelled) setReports(payload.reports);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load reports");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Reports
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Scored opportunity reports
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Ranked by overall priority. Open a report to inspect every score
        explanation and labeled claim.
      </p>

      {error && <p className="mt-6 text-amber-300">{error}</p>}

      <ul className="mt-8 space-y-4 border-t border-white/10 pt-6">
        {reports.map((report) => (
          <li key={report.id} className="flex flex-wrap items-baseline justify-between gap-3">
            <div>
              <Link
                href={`/reports/${report.id}`}
                className="text-lg text-white hover:text-teal-300"
              >
                {report.title}
              </Link>
              <p className="mt-1 text-sm text-zinc-400">{report.summary}</p>
            </div>
            <span className="font-mono text-sm text-teal-300">
              {report.scores.overall_priority.score.toFixed(2)}
            </span>
          </li>
        ))}
        {!error && reports.length === 0 && (
          <li className="text-zinc-400">
            No reports yet. Run discovery to generate the first one.
          </li>
        )}
      </ul>
    </main>
  );
}
