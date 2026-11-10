"use client";

import { IntelligencePanel } from "@/components/IntelligencePanel";

export default function AppIntelligencePage() {
  return (
    <IntelligencePanel
      title="App ecosystem intelligence"
      blurb="Placeholder surface for Play / App Store review gaps. Today it reuses SERP mock results filtered by the query — live store APIs arrive when credentials exist."
      providerHint="No fabricated ratings. Mock SERP only."
      endpoint="/providers/serp/search"
    />
  );
}
