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
      <section className="relative flex min-h-[72vh] flex-col justify-center py-6 md:min-h-[78vh] md:py-10">
        <div
          aria-hidden
          className="pointer-events-none absolute -left-10 top-8 h-56 w-56 rounded-full bg-[radial-gradient(circle,rgba(11,107,97,0.18),transparent_70%)] blur-2xl md:h-72 md:w-72"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute bottom-10 right-0 h-48 w-64 rounded-full bg-[radial-gradient(circle,rgba(42,63,57,0.12),transparent_70%)] blur-2xl"
        />

        <p className="page-kicker anim-fade">Opportunity intelligence</p>
        <h1 className="anim-rise mt-3 font-display text-[clamp(3.5rem,12vw,7.5rem)] font-medium leading-[0.9] tracking-tight text-ink">
          GUM
        </h1>
        <h2 className="anim-rise-delay mt-6 max-w-2xl font-display text-2xl font-medium tracking-tight text-ink-soft sm:text-3xl">
          Start with the problem, not the product.
        </h2>
        <p className="anim-rise-delay mt-4 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
          Collect evidence, surface gaps, compare formats, and score opportunities
          with labeled claims — never fabricated demand.
        </p>

        <div className="anim-rise-delay mt-8 flex flex-wrap gap-3">
          <Link href="/discover" className="btn-primary">
            Open discovery
          </Link>
          <Link href="/reports" className="btn-secondary">
            View reports
          </Link>
        </div>
      </section>

      <section className="section-rule">
        <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-muted">
          Backend status
        </h3>
        {error && (
          <p className="mt-3 text-warn">
            API unreachable at {API_BASE} ({error}). Start the FastAPI service.
          </p>
        )}
        {!error && health && (
          <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-5 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-muted">Status</dt>
              <dd className="mt-1 font-medium text-signal">{health.status}</dd>
            </div>
            <div>
              <dt className="text-muted">Version</dt>
              <dd className="mt-1 font-mono text-ink">{health.version}</dd>
            </div>
            <div>
              <dt className="text-muted">Database</dt>
              <dd className="mt-1 font-mono text-ink">{health.database}</dd>
            </div>
            <div>
              <dt className="text-muted">Reports</dt>
              <dd className="mt-1 font-mono text-ink">{reportCount ?? "—"}</dd>
            </div>
          </dl>
        )}
      </section>
    </main>
  );
}
