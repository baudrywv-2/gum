"use client";

import { IntelligencePanel } from "@/components/IntelligencePanel";

export default function XIntelligencePage() {
  return (
    <IntelligencePanel
      title="X intelligence"
      blurb="Recent conversation discovery signals from the X provider adapter. Discovery only — not purchase intent proof."
      providerHint="Mock mode by default (GUM_FORCE_MOCK_PROVIDERS)."
      endpoint="/providers/x_api/search"
    />
  );
}
