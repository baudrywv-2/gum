"use client";

import Link from "next/link";

export default function ValidationPage() {
  return (
    <main>
      <p className="text-sm uppercase tracking-[0.22em] text-teal-300/80">
        Validation
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        Cheapest experiments
      </h2>
      <p className="mt-3 max-w-2xl text-zinc-300">
        Track hypothesis → experiment → cost/time → success criteria → results →
        continue / pivot / abandon. Projected vs measured stay separate.
      </p>
      <p className="mt-8 border-t border-white/10 pt-6 text-zinc-400">
        Experiment tracking APIs ship in Milestone 10. Until then, open a{" "}
        <Link href="/reports" className="text-teal-300 hover:underline">
          scored report
        </Link>{" "}
        and use its cheapest validation experiment as the first step.
      </p>
    </main>
  );
}
