const STYLES: Record<string, string> = {
  MEASURED_FACT: "text-emerald-800 border-emerald-700/25 bg-emerald-50/80",
  PROVIDER_ESTIMATE: "text-sky-900 border-sky-700/25 bg-sky-50/80",
  AI_INTERPRETATION: "text-amber-900 border-amber-700/25 bg-amber-50/80",
  HYPOTHESIS: "text-teal-900 border-teal-700/25 bg-teal-50/70",
  UNVERIFIED_CLAIM: "text-ink-soft border-line-strong bg-white/70",
};

export function ClaimTagBadge({ tag }: { tag: string }) {
  return (
    <span
      className={`claim-badge ${
        STYLES[tag] ?? "text-ink-soft border-line-strong bg-white/70"
      }`}
    >
      {tag.replaceAll("_", " ")}
    </span>
  );
}
