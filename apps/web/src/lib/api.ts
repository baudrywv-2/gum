export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export type HealthPayload = {
  status: string;
  service: string;
  version: string;
  database: string;
  timestamp: string;
};

export type ScoreBlock = {
  dimension: string;
  score: number;
  weight: number;
  explanation: string;
  claims: { text: string; claim_tag: string; evidence_ids: string[] }[];
};

export type OpportunityReport = {
  id: string;
  collection_id: string;
  query: string;
  title: string;
  summary: string;
  problem: string;
  audience: string | null;
  geography: string | null;
  language: string | null;
  recommended_format: string | null;
  alternative_formats: string[];
  scores: {
    demand_evidence: ScoreBlock;
    organic_ranking_feasibility: ScoreBlock;
    format_fit: ScoreBlock;
    business_viability: ScoreBlock;
    evidence_confidence: ScoreBlock;
    overall_priority: ScoreBlock;
  };
  missing_info: string[];
  limitations: string[];
  next_actions: string[];
  cheapest_validation_experiment: string | null;
  competitors: string[];
  unmet_needs: { text: string; claim_tag: string }[];
  created_at?: string;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getHealth() {
  return api<HealthPayload>("/health");
}

export function listProviders() {
  return api<{
    providers: {
      name: string;
      mode: string;
      configured: boolean;
      notes: string;
    }[];
    force_mock: boolean;
  }>("/providers");
}

export type ResearchPlatformId = "youtube" | "serp" | "trends" | "x" | "all";

export type PlatformRun = {
  platform: string;
  provider: string;
  role: string;
  mode: string;
  claim_tag: string;
  item_count: number;
  skipped?: boolean;
  error?: string | null;
  notes?: string | null;
};

export const DEFAULT_RESEARCH_PLATFORMS: Exclude<ResearchPlatformId, "all">[] = [
  "trends",
  "serp",
  "youtube",
  "x",
];

export function collectEvidence(body: {
  query: string;
  geography?: string;
  language?: string;
  platforms?: ResearchPlatformId | ResearchPlatformId[];
}) {
  return api<{
    collection_id: string;
    evidence_created: number;
    pain_points_created: number;
    limitations: string[];
    platforms_requested: string[];
    platforms_run: PlatformRun[];
  }>("/evidence/collect", { method: "POST", body: JSON.stringify(body) });
}

export function discoverOpportunities(body: {
  query: string;
  geography?: string;
  language?: string;
  platforms?: ResearchPlatformId | ResearchPlatformId[];
}) {
  return api<{
    run_id: string;
    collection_id: string;
    opportunities: {
      id: string;
      title: string;
      summary: string;
      opportunity_type: string;
      claims: { text: string; claim_tag: string }[];
    }[];
    limitations: string[];
    platforms_requested: string[];
    platforms_run: PlatformRun[];
  }>("/opportunities/discover", { method: "POST", body: JSON.stringify(body) });
}

export function analyzeGaps(body: {
  query: string;
  geography?: string;
  language?: string;
}) {
  return api<{
    report_id: string;
    report: {
      competitors: { name: string; status: string }[];
      findings: { kind: string; title: string }[];
    };
  }>("/gaps/analyze", { method: "POST", body: JSON.stringify(body) });
}

export function recommendFormats(body: {
  query: string;
  geography?: string;
  language?: string;
}) {
  return api<{
    recommendation_id: string;
    recommendation: {
      primary_format: string;
      alternatives: string[];
      summary: string;
    };
  }>("/formats/recommend", { method: "POST", body: JSON.stringify(body) });
}

export function generateReports(body: {
  query: string;
  geography?: string;
  language?: string;
  platforms?: ResearchPlatformId | ResearchPlatformId[];
}) {
  return api<{
    reports: OpportunityReport[];
    count: number;
    limitations: string[];
    platforms_requested: string[];
    platforms_run: PlatformRun[];
  }>("/reports/generate", { method: "POST", body: JSON.stringify(body) });
}

export function listReports() {
  return api<{ reports: OpportunityReport[]; count: number }>("/reports");
}

export function getReport(id: string) {
  return api<OpportunityReport>(`/reports/${id}`);
}
