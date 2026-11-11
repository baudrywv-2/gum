"use client";

import { FormEvent, useState } from "react";
import { API_BASE } from "@/lib/api";

type Props = {
  title: string;
  blurb: string;
  providerHint: string;
  endpoint: string;
  method?: "GET" | "POST";
  bodyFactory?: (query: string) => unknown;
};

export function IntelligencePanel({
  title,
  blurb,
  providerHint,
  endpoint,
  method = "POST",
  bodyFactory,
}: Props) {
  const [query, setQuery] = useState("freelancer invoicing");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method,
        headers: { "content-type": "application/json" },
        body:
          method === "POST"
            ? JSON.stringify(
                bodyFactory
                  ? bodyFactory(query)
                  : { query, geography: "US", language: "en", limit: 5 },
              )
            : undefined,
        cache: "no-store",
      });
      const text = await response.text();
      if (!response.ok) throw new Error(text || `HTTP ${response.status}`);
      setPayload(JSON.stringify(JSON.parse(text), null, 2));
    } catch (err) {
      setPayload(null);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <p className="page-kicker">Intelligence</p>
      <h2 className="page-title">{title}</h2>
      <p className="page-lede">{blurb}</p>
      <p className="mt-2 text-sm text-muted">{providerHint}</p>

      <form onSubmit={onSubmit} className="section-rule flex flex-wrap gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="field-input min-w-[16rem] flex-1"
          required
        />
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? "Loading…" : "Query provider"}
        </button>
      </form>

      {error && <p className="mt-4 text-warn">{error}</p>}
      {payload && (
        <pre className="mt-6 max-h-[32rem] overflow-auto rounded-xl border border-line bg-white/75 p-4 font-mono text-xs text-ink-soft shadow-soft">
          {payload}
        </pre>
      )}
    </main>
  );
}
