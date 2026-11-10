"use client";

import { useEffect, useState } from "react";

type HealthPayload = {
  status: string;
  service: string;
  version: string;
  database: string;
  timestamp: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export default function Home() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}/health`, {
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = (await response.json()) as HealthPayload;
        if (!cancelled) {
          setHealth(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setHealth(null);
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,_#1a2332_0%,_#0b0f14_55%)] text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
        <p className="text-sm uppercase tracking-[0.2em] text-teal-300/80">
          Milestone 1 foundation
        </p>
        <h1 className="mt-3 text-5xl font-semibold tracking-tight text-white sm:text-6xl">
          GUM
        </h1>
        <p className="mt-4 max-w-xl text-lg text-zinc-300">
          Opportunity Intelligence Engine — monorepo scaffold with a Next.js
          shell, FastAPI health API, Postgres + Alembic, and shared contracts.
        </p>

        <section className="mt-10 border-t border-white/10 pt-8">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
            API health
          </h2>
          {loading && (
            <p className="mt-3 text-zinc-400">Checking {API_BASE}/health…</p>
          )}
          {!loading && error && (
            <p className="mt-3 text-amber-300">
              API unreachable ({error}). Start the backend per docs/setup.md.
            </p>
          )}
          {!loading && health && (
            <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-zinc-500">Status</dt>
                <dd className="mt-1 font-medium text-teal-300">{health.status}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Database</dt>
                <dd className="mt-1 font-medium">{health.database}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Service</dt>
                <dd className="mt-1 font-medium">{health.service}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Version</dt>
                <dd className="mt-1 font-medium">{health.version}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-zinc-500">Timestamp</dt>
                <dd className="mt-1 font-medium">{health.timestamp}</dd>
              </div>
            </dl>
          )}
        </section>
      </div>
    </main>
  );
}
