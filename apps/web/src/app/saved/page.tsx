"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getReport, type OpportunityReport } from "@/lib/api";

const SAVED_KEY = "gum.savedReportIds";

export default function SavedPage() {
  const [reports, setReports] = useState<OpportunityReport[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const ids = JSON.parse(localStorage.getItem(SAVED_KEY) || "[]") as string[];
        const loaded = await Promise.all(
          ids.map(async (id) => {
            try {
              return await getReport(id);
            } catch {
              return null;
            }
          }),
        );
        if (!cancelled) {
          setReports(loaded.filter((r): r is OpportunityReport => r !== null));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load saved");
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">Saved</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Saved opportunities
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Local bookmarks of scored reports. Server-side workspace saves land with
        auth later; until then IDs stay in this browser.
      </p>
      {error && <p className="mt-6 text-amber-300">{error}</p>}
      <ul className="mt-8 space-y-3 border-t border-white/10 pt-6">
        {reports.map((report) => (
          <li key={report.id}>
            <Link
              href={`/reports/${report.id}`}
              className="text-lg text-white hover:text-teal-300"
            >
              {report.title}
            </Link>
            <p className="text-sm text-zinc-400">
              Priority {report.scores.overall_priority.score.toFixed(2)} ·{" "}
              {report.recommended_format ?? "no format"}
            </p>
          </li>
        ))}
        {reports.length === 0 && (
          <li className="text-zinc-400">
            Nothing saved yet. Use Save on a discovery result.
          </li>
        )}
      </ul>
    </main>
  );
}
