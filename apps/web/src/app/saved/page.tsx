"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getReport, type OpportunityReport } from "@/lib/api";

const SAVED_KEY = "gum.savedReportIds";

export default function SavedPage() {
  const [reports, setReports] = useState<OpportunityReport[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

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
          setReady(true);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load saved");
          setReady(true);
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
      <p className="page-kicker">Saved</p>
      <h2 className="page-title">Saved opportunities</h2>
      <p className="page-lede">
        Local bookmarks of scored reports. Server-side workspace saves land with
        auth later; until then IDs stay in this browser.
      </p>

      {error && <p className="mt-6 text-warn">{error}</p>}

      {ready && reports.length === 0 && !error && (
        <div className="section-rule">
          <div className="max-w-lg rounded-2xl border border-line bg-white/70 p-8 shadow-soft">
            <p className="font-display text-2xl font-medium text-ink">
              Nothing saved yet
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              Run Discovery, open a ranked report, then hit Save. Bookmarks stay
              on this device until workspace sync ships.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/discover" className="btn-primary">
                Research a problem
              </Link>
              <Link href="/reports" className="btn-secondary">
                Browse reports
              </Link>
            </div>
          </div>
        </div>
      )}

      {reports.length > 0 && (
        <ul className="section-rule space-y-4">
          {reports.map((report) => (
            <li key={report.id}>
              <Link
                href={`/reports/${report.id}`}
                className="group block rounded-xl border border-transparent px-1 py-2 transition hover:border-line hover:bg-white/60"
              >
                <span className="text-lg font-medium text-ink group-hover:text-signal">
                  {report.title}
                </span>
                <p className="mt-1 text-sm text-muted">
                  Priority {report.scores.overall_priority.score.toFixed(2)} ·{" "}
                  {report.recommended_format ?? "no format"}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
