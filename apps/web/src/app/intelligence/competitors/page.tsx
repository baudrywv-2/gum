"use client";

import { IntelligencePanel } from "@/components/IntelligencePanel";

export default function CompetitorIntelligencePage() {
  return (
    <IntelligencePanel
      title="Competitor intelligence"
      blurb="Runs gap analysis: existing solutions from search vs feedback. Competitors are never labeled weak without complaint-backed evidence."
      providerHint="POST /gaps/analyze on the shared backend."
      endpoint="/gaps/analyze"
      bodyFactory={(query) => ({
        query,
        geography: "US",
        language: "en",
        collect_if_missing: true,
      })}
    />
  );
}
