"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ClaimTagBadge } from "@/components/ClaimTag";
import { PlatformChips } from "@/components/PlatformChips";
import { ScoreBar } from "@/components/ScoreBar";
import {
  DEFAULT_RESEARCH_PLATFORMS,
  generateReports,
  type OpportunityReport,
  type PlatformRun,
  type ResearchPlatformId,
} from "@/lib/api";

const SAVED_KEY = "gum.savedReportIds";

function saveReportId(id: string) {
  const existing = JSON.parse(localStorage.getItem(SAVED_KEY) || "[]") as string[];
  if (!existing.includes(id)) {
    localStorage.setItem(SAVED_KEY, JSON.stringify([id, ...existing]));
  }
}

function modeClass(mode: string) {
  if (mode === "live") return "text-emerald-300";
  if (mode === "unavailable") return "text-amber-300";
  return "text-zinc-400";
}

export default function DiscoverPage() {
  const [query, setQuery] = useState("freelancer invoicing calculator tool");
  const [geography, setGeography] = useState("US");
  const [language, setLanguage] = useState("en");
  const [platforms, setPlatforms] = useState<
    Array<Exclude<ResearchPlatformId, "all">>
  >([...DEFAULT_RESEARCH_PLATFORMS]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reports, setReports] = useState<OpportunityReport[]>([]);
  const [limitations, setLimitations] = useState<string[]>([]);
  const [platformsRequested, setPlatformsRequested] = useState<string[]>([]);
  const [platformsRun, setPlatformsRun] = useState<PlatformRun[]>([]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const selected =
        platforms.length === DEFAULT_RESEARCH_PLATFORMS.length
          ? ("all" as const)
          : platforms;
      const result = await generateReports({
        query: query.trim(),
        geography: geography || undefined,
        language: language || undefined,
        platforms: selected,
      });
      setReports(result.reports);
      setLimitations(result.limitations);
      setPlatformsRequested(result.platforms_requested ?? []);
      setPlatformsRun(result.platforms_run ?? []);
    } catch (err) {
      setReports([]);
      setPlatformsRun([]);
      setPlatformsRequested([]);
      setError(err instanceof Error ? err.message : "Discovery failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Opportunity discovery
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Research a problem space
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Pick one platform, a combination, or all. Runs evidence collection through
        the shared API with labeled claims — no fabricated demand.
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-8 space-y-5 border-t border-white/10 pt-8"
      >
        <label className="block">
          <span className="text-xs uppercase tracking-wider text-zinc-500">
            Query
          </span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="mt-1 w-full rounded-md border border-white/15 bg-black/20 px-3 py-2 text-zinc-100 outline-none focus:border-teal-400/50"
            required
          />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-xs uppercase tracking-wider text-zinc-500">
              Geography
            </span>
            <input
              value={geography}
              onChange={(e) => setGeography(e.target.value)}
              className="mt-1 w-full rounded-md border border-white/15 bg-black/20 px-3 py-2 text-zinc-100 outline-none focus:border-teal-400/50"
            />
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-wider text-zinc-500">
              Language
            </span>
            <input
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="mt-1 w-full rounded-md border border-white/15 bg-black/20 px-3 py-2 text-zinc-100 outline-none focus:border-teal-400/50"
            />
          </label>
        </div>

        <PlatformChips
          selected={platforms}
          onChange={setPlatforms}
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-teal-400 px-5 py-2.5 text-sm font-medium text-zinc-950 disabled:opacity-60"
        >
          {loading ? "Running pipeline…" : "Discover & score"}
        </button>
      </form>

      {error && <p className="mt-6 text-amber-300">{error}</p>}

      {platformsRun.length > 0 && (
        <section className="mt-10 border-t border-white/10 pt-6">
          <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
            Sources that ran
          </h3>
          {platformsRequested.length > 0 && (
            <p className="mt-2 text-xs text-zinc-500">
              Requested: {platformsRequested.join(", ")}
            </p>
          )}
          <ul className="mt-4 space-y-3">
            {platformsRun.map((run) => (
              <li
                key={`${run.platform}-${run.provider}-${run.role}`}
                className="flex flex-wrap items-center gap-3 text-sm"
              >
                <span className="min-w-24 font-medium text-zinc-100">
                  {run.platform}
                </span>
                <span className={`uppercase tracking-wide ${modeClass(run.mode)}`}>
                  {run.mode}
                </span>
                <ClaimTagBadge tag={run.claim_tag} />
                <span className="text-zinc-500">
                  {run.item_count} item{run.item_count === 1 ? "" : "s"}
                  {run.role ? ` · ${run.role}` : ""}
                </span>
                {run.error ? (
                  <span className="text-amber-300/90">{run.error}</span>
                ) : null}
                {run.notes ? (
                  <span className="text-zinc-500">{run.notes}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      )}

      {reports.length > 0 && (
        <section className="mt-10 space-y-8">
          <h3 className="text-sm font-medium uppercase tracking-wider text-zinc-400">
            Ranked reports ({reports.length})
          </h3>
          {reports.map((report) => (
            <article
              key={report.id}
              className="border-t border-white/10 pt-6"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h4 className="text-xl font-medium text-white">
                    {report.title}
                  </h4>
                  <p className="mt-2 max-w-3xl text-sm text-zinc-300">
                    {report.summary}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => saveReportId(report.id)}
                    className="rounded-md border border-white/15 px-3 py-1.5 text-xs text-zinc-200 hover:bg-white/5"
                  >
                    Save
                  </button>
                  <Link
                    href={`/reports/${report.id}`}
                    className="rounded-md border border-white/15 px-3 py-1.5 text-xs text-zinc-200 hover:bg-white/5"
                  >
                    Open
                  </Link>
                </div>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <ScoreBar
                  label="Overall priority"
                  score={report.scores.overall_priority.score}
                  explanation={report.scores.overall_priority.explanation}
                />
                <ScoreBar
                  label="Evidence confidence"
                  score={report.scores.evidence_confidence.score}
                  explanation={report.scores.evidence_confidence.explanation}
                />
                <ScoreBar
                  label="Demand evidence"
                  score={report.scores.demand_evidence.score}
                  explanation={report.scores.demand_evidence.explanation}
                />
                <ScoreBar
                  label="Format fit"
                  score={report.scores.format_fit.score}
                  explanation={report.scores.format_fit.explanation}
                />
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {report.scores.overall_priority.claims.slice(0, 2).map((claim) => (
                  <div key={claim.text} className="flex items-center gap-2">
                    <ClaimTagBadge tag={claim.claim_tag} />
                    <span className="text-xs text-zinc-400">{claim.text}</span>
                  </div>
                ))}
              </div>

              <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
                <div>
                  <dt className="text-zinc-500">Recommended format</dt>
                  <dd className="mt-1 text-zinc-200">
                    {report.recommended_format ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Cheapest validation</dt>
                  <dd className="mt-1 text-zinc-200">
                    {report.cheapest_validation_experiment ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Competitors observed</dt>
                  <dd className="mt-1 text-zinc-200">
                    {report.competitors.length
                      ? report.competitors.slice(0, 4).join(", ")
                      : "—"}
                  </dd>
                </div>
              </dl>
            </article>
          ))}

          {limitations.length > 0 && (
            <div className="border-t border-white/10 pt-4">
              <h4 className="text-xs uppercase tracking-wider text-zinc-500">
                Limitations
              </h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-zinc-400">
                {limitations.slice(0, 8).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
