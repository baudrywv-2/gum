"use client";

import { API_BASE } from "@/lib/api";

export default function SettingsPage() {
  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Settings
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Workspace preferences
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Transparent defaults for skilled operators. Auth, budgets, and live
        credential vaults stay out of scope until secrets are available.
      </p>

      <dl className="mt-8 space-y-4 border-t border-white/10 pt-6 text-sm">
        <div>
          <dt className="text-zinc-500">API base URL</dt>
          <dd className="mt-1 font-mono text-zinc-200">{API_BASE}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Claim labeling</dt>
          <dd className="mt-1 text-zinc-200">
            Required on every recommendation (MEASURED FACT · PROVIDER ESTIMATE ·
            AI INTERPRETATION · HYPOTHESIS · UNVERIFIED CLAIM).
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">Demand fabrication</dt>
          <dd className="mt-1 text-zinc-200">Forbidden. Scores never invent volumes.</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Provider mode</dt>
          <dd className="mt-1 text-zinc-200">
            Mock unless credentials exist and GUM_FORCE_MOCK_PROVIDERS is false.
          </dd>
        </div>
      </dl>
    </main>
  );
}
