export function ScoreBar({
  label,
  score,
  explanation,
}: {
  label: string;
  score: number;
  explanation: string;
}) {
  const pct = Math.round(score * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-zinc-200">{label}</span>
        <span className="font-mono text-sm text-teal-300">{score.toFixed(2)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded bg-white/10">
        <div
          className="h-full rounded bg-teal-400/80"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs leading-relaxed text-zinc-500">{explanation}</p>
    </div>
  );
}
