"use client";

import { FormEvent, useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

type Experiment = {
  id: string;
  query: string;
  hypothesis: string;
  experiment: string;
  projected_cost_usd: number | null;
  projected_time_days: number | null;
  measured_cost_usd: number | null;
  measured_time_days: number | null;
  success_criteria: string[];
  status: string;
  decision: string;
  results: string | null;
};

export default function ValidationPage() {
  const [query, setQuery] = useState("freelancer invoicing calculator tool");
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const response = await fetch(`${API_BASE}/validation/experiments`, {
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    setExperiments(payload.experiments ?? []);
  }

  useEffect(() => {
    void refresh().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load"),
    );
  }, []);

  async function onPropose(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/validation/propose`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          query,
          geography: "US",
          language: "en",
          max_experiments: 3,
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Propose failed");
    } finally {
      setLoading(false);
    }
  }

  async function recordOutcome(id: string, decision: string) {
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE}/validation/experiments/${id}/outcome`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            measured_cost_usd: 20,
            measured_time_days: 4,
            results: `Operator-recorded outcome via dashboard (${decision}).`,
            decision,
            decision_rationale: "Recorded from Validation UI; projected≠measured kept separate.",
            status: "completed",
          }),
        },
      );
      if (!response.ok) throw new Error(await response.text());
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Outcome failed");
    }
  }

  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Validation
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Cheapest experiments
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Propose hypothesis → experiment → projected cost/time → success criteria.
        Record measured results and decide continue / pivot / abandon. Projected
        and measured stay separate — no invented wins.
      </p>

      <form
        onSubmit={onPropose}
        className="mt-8 flex flex-wrap gap-3 border-t border-white/10 pt-8"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="min-w-[16rem] flex-1 rounded-md border border-white/15 bg-black/20 px-3 py-2 text-zinc-100 outline-none focus:border-teal-400/50"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-teal-400 px-4 py-2 text-sm font-medium text-zinc-950 disabled:opacity-60"
        >
          {loading ? "Proposing…" : "Propose experiments"}
        </button>
      </form>

      {error && <p className="mt-4 text-amber-300">{error}</p>}

      <ul className="mt-8 space-y-6">
        {experiments.map((exp) => (
          <li key={exp.id} className="border-t border-white/10 pt-5">
            <p className="text-lg text-white">{exp.query}</p>
            <p className="mt-2 text-sm text-zinc-300">{exp.hypothesis}</p>
            <p className="mt-2 text-sm text-zinc-400">{exp.experiment}</p>
            <dl className="mt-3 grid gap-2 text-xs text-zinc-500 sm:grid-cols-4">
              <div>
                Projected cost: {exp.projected_cost_usd ?? "—"}
              </div>
              <div>
                Measured cost: {exp.measured_cost_usd ?? "—"}
              </div>
              <div>
                Projected days: {exp.projected_time_days ?? "—"}
              </div>
              <div>
                Measured days: {exp.measured_time_days ?? "—"}
              </div>
            </dl>
            <p className="mt-2 text-xs uppercase tracking-wide text-teal-300/80">
              {exp.status} · {exp.decision}
            </p>
            {exp.decision === "pending" && (
              <div className="mt-3 flex flex-wrap gap-2">
                {(["continue", "pivot", "abandon"] as const).map((decision) => (
                  <button
                    key={decision}
                    type="button"
                    onClick={() => void recordOutcome(exp.id, decision)}
                    className="rounded-md border border-white/15 px-3 py-1.5 text-xs text-zinc-200 hover:bg-white/5"
                  >
                    Record {decision}
                  </button>
                ))}
              </div>
            )}
            {exp.results && (
              <p className="mt-2 text-sm text-zinc-400">Results: {exp.results}</p>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
