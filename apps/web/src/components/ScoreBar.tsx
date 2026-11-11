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
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-ink-soft">{label}</span>
        <span className="font-mono text-sm text-signal">{score.toFixed(2)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-ink/10">
        <div
          className="h-full rounded-full bg-signal/85 transition-[width] duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs leading-relaxed text-muted">{explanation}</p>
    </div>
  );
}
