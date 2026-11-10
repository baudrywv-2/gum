"use client";

import { IntelligencePanel } from "@/components/IntelligencePanel";

export default function CommunityIntelligencePage() {
  return (
    <IntelligencePanel
      title="Community intelligence"
      blurb="Discussion-style evidence via the mock community provider path. Pain extraction happens in the evidence engine."
      providerHint="Wired through /providers/mock/search until Reddit/forum adapters are live."
      endpoint="/providers/mock/search"
    />
  );
}
