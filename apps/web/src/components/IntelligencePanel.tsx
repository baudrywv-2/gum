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
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Intelligence
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        {title}
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">{blurb}</p>
      <p className="mt-2 text-sm text-zinc-500">{providerHint}</p>

      <form onSubmit={onSubmit} className="mt-8 flex flex-wrap gap-3 border-t border-white/10 pt-8">
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
          {loading ? "Loading…" : "Query provider"}
        </button>
      </form>

      {error && <p className="mt-4 text-amber-300">{error}</p>}
      {payload && (
        <pre className="mt-6 max-h-[32rem] overflow-auto rounded-md border border-white/10 bg-black/30 p-4 text-xs text-zinc-300">
          {payload}
        </pre>
      )}
    </main>
  );
}
