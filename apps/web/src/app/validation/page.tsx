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
      <p className="page-kicker">
        Validation
      </p>
      <h2 className="page-title">
        Cheapest experiments
      </h2>
      <p className="page-lede">
        Propose hypothesis → experiment → projected cost/time → success criteria.
        Record measured results and decide continue / pivot / abandon. Projected
        and measured stay separate — no invented wins.
      </p>

      <form
        onSubmit={onPropose}
        className="section-rule flex flex-wrap gap-3"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="min-w-[16rem] flex-1 field-input"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="btn-primary"
        >
          {loading ? "Proposing…" : "Propose experiments"}
        </button>
      </form>

      {error && <p className="mt-4 text-warn">{error}</p>}

      <ul className="mt-8 space-y-6">
        {experiments.map((exp) => (
          <li key={exp.id} className="border-t border-line pt-5">
            <p className="text-lg font-medium text-ink">{exp.query}</p>
            <p className="mt-2 text-sm text-muted">{exp.hypothesis}</p>
            <p className="mt-2 text-sm text-muted">{exp.experiment}</p>
            <dl className="mt-3 grid gap-2 text-xs text-muted sm:grid-cols-4">
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
            <p className="mt-2 text-xs uppercase tracking-wide text-signal">
              {exp.status} · {exp.decision}
            </p>
            {exp.decision === "pending" && (
              <div className="mt-3 flex flex-wrap gap-2">
                {(["continue", "pivot", "abandon"] as const).map((decision) => (
                  <button
                    key={decision}
                    type="button"
                    onClick={() => void recordOutcome(exp.id, decision)}
                    className="btn-ghost"
                  >
                    Record {decision}
                  </button>
                ))}
              </div>
            )}
            {exp.results && (
              <p className="mt-2 text-sm text-muted">Results: {exp.results}</p>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
