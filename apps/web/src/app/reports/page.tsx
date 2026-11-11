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
      <p className="page-kicker">Reports</p>
      <h2 className="page-title">Scored opportunity reports</h2>
      <p className="page-lede">
        Ranked by overall priority. Open a report to inspect every score
        explanation and labeled claim.
      </p>

      {error && <p className="mt-6 text-warn">{error}</p>}

      <ul className="section-rule space-y-4">
        {reports.map((report) => (
          <li
            key={report.id}
            className="flex flex-wrap items-baseline justify-between gap-3"
          >
            <div>
              <Link
                href={`/reports/${report.id}`}
                className="text-lg font-medium text-ink hover:text-signal"
              >
                {report.title}
              </Link>
              <p className="mt-1 text-sm text-muted">{report.summary}</p>
            </div>
            <span className="font-mono text-sm text-signal">
              {report.scores.overall_priority.score.toFixed(2)}
            </span>
          </li>
        ))}
        {!error && reports.length === 0 && (
          <li className="text-muted">
            No reports yet.{" "}
            <Link href="/discover" className="text-signal underline-offset-2 hover:underline">
              Run discovery
            </Link>{" "}
            to generate the first one.
          </li>
        )}
      </ul>
    </main>
  );
}
