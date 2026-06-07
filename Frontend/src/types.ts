export type PipelineEvent = {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
};

export type WebhookEvent = {
  delivery_id: string;
  event: 'push' | 'pull_request' | 'ping' | string;
  repo: string;
  received_at: string;
  session_id: string | null;
  status: 'pipeline_triggered' | 'pong' | 'ignored' | 'received' | string;
  branch?: string;
};

export type PipelineRunState = {
  sessionId: string;
  isRunning: boolean;
  currentStage: string | null;
  completedStages: string[];
  events: PipelineEvent[];
  finalPayload: FinalPayload | null;
  error: string | null;
};

export type FinalPayload = {
  session_id: string;
  pipeline_metadata: {
    author: string;
    changed_files: string[];
    classification: {
      cloud_infra: string[];
      git_meta: string[];
      app_code: string[];
    };
    github_repo?: string;
    github_data?: {
      commits?: Array<{ sha: string; message: string; author: string; date: string }>;
      issues?: Array<{ number: number; title: string; state: string; created_at: string }>;
    };
  };
  triage_layer: {
    risk_flagged: boolean;
    matches_found: number;
    reasoning: string;
  };
  expert_analysis: {
    cloud_expert_notes: string;
    code_expert_notes: string;
    git_expert_notes: string;
  };
  final_audit_report: {
    verdict: 'APPROVED' | 'BLOCKED' | 'REQUIRES_REVIEW';
    risks: string[];
    mitigation_patches: string[];
    example_patch_code: string;
    conclusion: string;
  };
};
