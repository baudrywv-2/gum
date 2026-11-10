"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

type ProviderRow = {
  name: string;
  mode: string;
  configured: boolean;
  notes: string;
};

export default function IntegrationsPage() {
  const [providers, setProviders] = useState<ProviderRow[]>([]);
  const [forceMock, setForceMock] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/providers`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((payload) => {
        if (!cancelled) {
          setProviders(payload.providers ?? []);
          setForceMock(Boolean(payload.force_mock));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load providers");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Integrations
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Provider adapters
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Modular, replaceable data sources. Mock by default — no paid calls unless
        credentials exist and mock force is off.
      </p>
      {forceMock !== null && (
        <p className="mt-4 text-sm text-zinc-400">
          Force mock:{" "}
          <span className="text-teal-300">{forceMock ? "on" : "off"}</span>
        </p>
      )}
      {error && <p className="mt-6 text-amber-300">{error}</p>}
      <ul className="mt-8 space-y-4 border-t border-white/10 pt-6">
        {providers.map((provider) => (
          <li key={provider.name} className="flex flex-wrap items-baseline justify-between gap-3">
            <div>
              <p className="text-lg text-white">{provider.name}</p>
              <p className="text-sm text-zinc-400">{provider.notes}</p>
            </div>
            <div className="text-right text-sm">
              <p className="text-teal-300">{provider.mode}</p>
              <p className="text-zinc-500">
                {provider.configured ? "configured" : "not configured"}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
