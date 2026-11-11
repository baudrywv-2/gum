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
      <p className="page-kicker">
        Integrations
      </p>
      <h2 className="page-title">
        Provider adapters
      </h2>
      <p className="page-lede">
        Modular, replaceable data sources. Mock by default — no paid calls unless
        credentials exist and mock force is off.
      </p>
      {forceMock !== null && (
        <p className="mt-4 text-sm text-muted">
          Force mock:{" "}
          <span className="text-signal">{forceMock ? "on" : "off"}</span>
        </p>
      )}
      {error && <p className="mt-6 text-warn">{error}</p>}
      <ul className="section-rule space-y-4">
        {providers.map((provider) => (
          <li key={provider.name} className="flex flex-wrap items-baseline justify-between gap-3">
            <div>
              <p className="text-lg text-ink">{provider.name}</p>
              <p className="text-sm text-muted">{provider.notes}</p>
            </div>
            <div className="text-right text-sm">
              <p className="text-signal">{provider.mode}</p>
              <p className="text-muted">
                {provider.configured ? "configured" : "not configured"}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
