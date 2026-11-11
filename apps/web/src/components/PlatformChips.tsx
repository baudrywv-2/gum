"use client";

import {
  DEFAULT_RESEARCH_PLATFORMS,
  type ResearchPlatformId,
} from "@/lib/api";

const CHIP_META: {
  id: Exclude<ResearchPlatformId, "all"> | "all";
  label: string;
  hint: string;
}[] = [
  { id: "all", label: "All", hint: "Trends + SERP + YouTube + X" },
  { id: "trends", label: "Trends", hint: "SerpAPI Google Trends" },
  { id: "serp", label: "SERP", hint: "SerpAPI Google organic" },
  { id: "youtube", label: "YouTube", hint: "YouTube Data API v3" },
  { id: "x", label: "X", hint: "X recent search (discussion)" },
];

type Props = {
  selected: Array<Exclude<ResearchPlatformId, "all">>;
  onChange: (next: Array<Exclude<ResearchPlatformId, "all">>) => void;
  disabled?: boolean;
};

export function PlatformChips({ selected, onChange, disabled }: Props) {
  const allSelected =
    selected.length === DEFAULT_RESEARCH_PLATFORMS.length &&
    DEFAULT_RESEARCH_PLATFORMS.every((id) => selected.includes(id));

  function toggle(id: (typeof CHIP_META)[number]["id"]) {
    if (disabled) return;
    if (id === "all") {
      onChange([...DEFAULT_RESEARCH_PLATFORMS]);
      return;
    }
    const has = selected.includes(id);
    let next = has ? selected.filter((x) => x !== id) : [...selected, id];
    if (next.length === 0) {
      next = [...DEFAULT_RESEARCH_PLATFORMS];
    }
    onChange(next);
  }

  return (
    <fieldset disabled={disabled} className="block">
      <legend className="field-label">Platforms</legend>
      <p className="mt-1.5 text-xs leading-relaxed text-muted">
        Research one source, a combination, or all. Unselected providers are
        skipped — no synthetic fill-in.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {CHIP_META.map((chip) => {
          const active =
            chip.id === "all" ? allSelected : selected.includes(chip.id);
          return (
            <button
              key={chip.id}
              type="button"
              title={chip.hint}
              aria-pressed={active}
              onClick={() => toggle(chip.id)}
              className={`rounded-lg border px-3.5 py-2 text-xs font-medium tracking-wide transition ${
                active
                  ? "border-signal/50 bg-signal text-white shadow-soft"
                  : "border-line-strong bg-white/55 text-ink-soft hover:border-ink/25 hover:bg-white"
              }`}
            >
              {chip.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
