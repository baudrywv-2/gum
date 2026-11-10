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
      <legend className="text-xs uppercase tracking-wider text-zinc-500">
        Platforms
      </legend>
      <p className="mt-1 text-xs text-zinc-500">
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
              className={`rounded-full border px-3 py-1.5 text-xs tracking-wide transition ${
                active
                  ? "border-teal-400/60 bg-teal-400/15 text-teal-100"
                  : "border-white/15 bg-transparent text-zinc-400 hover:border-white/30 hover:text-zinc-200"
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
