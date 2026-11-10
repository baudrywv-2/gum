"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_BASE, getHealth, listReports, type HealthPayload } from "@/lib/api";

export default function OverviewPage() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [reportCount, setReportCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [h, reports] = await Promise.all([
          getHealth(),
          listReports().catch(() => ({ count: 0, reports: [] })),
        ]);
        if (!cancelled) {
          setHealth(h);
          setReportCount(reports.count);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "API unreachable");
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
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Discovery-first workspace
      </p>
      <h2 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
        Start with the problem, not the product.
      </h2>
      <p className="mt-4 max-w-2xl text-lg text-zinc-300">
        GUM collects evidence, surfaces gaps, compares solution formats, and
        scores opportunities with labeled claims — never fabricated demand.
      </p>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/discover"
          className="rounded-md bg-teal-400 px-5 py-2.5 text-sm font-medium text-zinc-950 hover:bg-teal-300"
        >
          Open discovery
        </Link>
        <Link
          href="/reports"
          className="rounded-md border border-white/15 px-5 py-2.5 text-sm text-zinc-100 hover:bg-white/5"
        >
          View reports
        </Link>
      </div>

      <section className="mt-12 border-t border-white/10 pt-8">
        <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
          Backend status
        </h3>
        {error && (
          <p className="mt-3 text-amber-300">
            API unreachable at {API_BASE} ({error}). Start the FastAPI service.
          </p>
        )}
        {!error && health && (
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-zinc-500">Status</dt>
              <dd className="mt-1 text-teal-300">{health.status}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Version</dt>
              <dd className="mt-1">{health.version}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Database</dt>
              <dd className="mt-1">{health.database}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Reports</dt>
              <dd className="mt-1">{reportCount ?? "—"}</dd>
            </div>
          </dl>
        )}
      </section>
    </main>
  );
}
