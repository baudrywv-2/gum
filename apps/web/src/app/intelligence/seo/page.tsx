"use client";

import { IntelligencePanel } from "@/components/IntelligencePanel";

export default function SeoIntelligencePage() {
  return (
    <IntelligencePanel
      title="SEO intelligence"
      blurb="Inspect Google Ads / Trends / SERP mock signals for a query. Social buzz is never treated as market size."
      providerHint="Uses mock providers unless live credentials are configured."
      endpoint="/providers/serp/search"
    />
  );
}
