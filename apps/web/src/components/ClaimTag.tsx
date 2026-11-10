const STYLES: Record<string, string> = {
  MEASURED_FACT: "text-emerald-300 border-emerald-400/30",
  PROVIDER_ESTIMATE: "text-sky-300 border-sky-400/30",
  AI_INTERPRETATION: "text-amber-200 border-amber-400/30",
  HYPOTHESIS: "text-teal-200 border-teal-400/30",
  UNVERIFIED_CLAIM: "text-zinc-300 border-zinc-500/40",
};

export function ClaimTagBadge({ tag }: { tag: string }) {
  return (
    <span
      className={`inline-flex rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
        STYLES[tag] ?? "text-zinc-300 border-zinc-500/40"
      }`}
    >
      {tag.replaceAll("_", " ")}
    </span>
  );
}
