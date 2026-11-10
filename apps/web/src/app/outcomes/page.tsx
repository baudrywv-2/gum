"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

type Outcome = {
  experiment_id: string;
  query: string;
  hypothesis: string;
  decision: string;
  projected_cost_usd: number | null;
  measured_cost_usd: number | null;
  projected_time_days: number | null;
  measured_time_days: number | null;
  results: string | null;
};

export default function OutcomesPage() {
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/validation/outcomes`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((payload) => {
        if (!cancelled) setOutcomes(payload.outcomes ?? []);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load outcomes");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Outcomes
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Learn from measured results
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Continue / pivot / abandon decisions with projected vs measured cost and
        time kept distinct. No fabricated wins.
      </p>

      {error && <p className="mt-6 text-amber-300">{error}</p>}

      <ul className="mt-8 space-y-5 border-t border-white/10 pt-6">
        {outcomes.map((outcome) => (
          <li key={outcome.experiment_id}>
            <p className="text-lg text-white">{outcome.query}</p>
            <p className="mt-1 text-sm text-zinc-400">{outcome.hypothesis}</p>
            <p className="mt-2 text-sm text-teal-300 uppercase tracking-wide">
              {outcome.decision}
            </p>
            <p className="mt-2 text-xs text-zinc-500">
              Projected ${outcome.projected_cost_usd ?? "—"} /{" "}
              {outcome.projected_time_days ?? "—"}d · Measured $
              {outcome.measured_cost_usd ?? "—"} / {outcome.measured_time_days ?? "—"}d
            </p>
            {outcome.results && (
              <p className="mt-2 text-sm text-zinc-300">{outcome.results}</p>
            )}
          </li>
        ))}
        {!error && outcomes.length === 0 && (
          <li className="text-zinc-400">
            No recorded outcomes yet. Propose an experiment on Validation and
            record a decision.
          </li>
        )}
      </ul>
    </main>
  );
}
