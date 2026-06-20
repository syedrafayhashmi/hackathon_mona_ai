export type ModuleDefinition = {
  id: string;
  name: string;
  group: string;
  description: string;
  fixtures: { id: string; label: string }[];
  action_label: string;
};

export type AuditEvent = {
  stage: string;
  title: string;
  detail: string;
  status: "complete" | "review" | "blocked" | "pending";
  at: string;
};

export type FileStatus = {
  name: string;
  status: "pending" | "processing" | "completed" | "failed";
  detail: string;
};

export type RunRecord = {
  id: string;
  problem_id: string;
  module_name: string;
  fixture_id?: string;
  status: "completed" | "approved" | "actioned" | "blocked" | "failed";
  confidence: number;
  source_mode: "deterministic" | "gemini" | "fallback";
  agent_generated: boolean;
  model_usage: string[];
  decision: string;
  requires_approval: boolean;
  approved: boolean;
  created_at: string;
  result: {
    summary: string;
    table: { columns: string[]; rows: Record<string, unknown>[] };
    evidence: string[];
    warnings: string[];
    review: Record<string, unknown>;
    artifacts: string[];
  };
  audit_events: AuditEvent[];
  file_statuses?: FileStatus[];
};

export type Health = {
  status: string;
  gemini: boolean;
  agents: boolean;
  ffmpeg: boolean;
  models?: Record<string, string>;
};
