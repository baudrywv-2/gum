"use client";

import { API_BASE } from "@/lib/api";

export default function SettingsPage() {
  return (
    <main>
      <p className="page-kicker">
        Settings
      </p>
      <h2 className="page-title">
        Workspace preferences
      </h2>
      <p className="page-lede">
        Transparent defaults for skilled operators. Auth, budgets, and live
        credential vaults stay out of scope until secrets are available.
      </p>

      <dl className="section-rule space-y-4 text-sm">
        <div>
          <dt className="text-muted">API base URL</dt>
          <dd className="mt-1 font-mono text-ink-soft">{API_BASE}</dd>
        </div>
        <div>
          <dt className="text-muted">Claim labeling</dt>
          <dd className="mt-1 text-ink-soft">
            Required on every recommendation (MEASURED FACT · PROVIDER ESTIMATE ·
            AI INTERPRETATION · HYPOTHESIS · UNVERIFIED CLAIM).
          </dd>
        </div>
        <div>
          <dt className="text-muted">Demand fabrication</dt>
          <dd className="mt-1 text-ink-soft">Forbidden. Scores never invent volumes.</dd>
        </div>
        <div>
          <dt className="text-muted">Provider mode</dt>
          <dd className="mt-1 text-ink-soft">
            Mock unless credentials exist and GUM_FORCE_MOCK_PROVIDERS is false.
          </dd>
        </div>
      </dl>
    </main>
  );
}
