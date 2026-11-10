"use client";

import { IntelligencePanel } from "@/components/IntelligencePanel";

export default function YoutubeIntelligencePage() {
  return (
    <IntelligencePanel
      title="YouTube intelligence"
      blurb="Topic and content-gap exploration. Without YouTube Data API credentials, this panel uses the mock SERP adapter and labels results as unverified."
      providerHint="Live YouTube client deferred until credentials exist."
      endpoint="/providers/serp/search"
    />
  );
}
