/**
 * Agent workspace types.
 * Mirrors backend agent/workflow schema shapes.
 *
 * Rules:
 *   - Field names match backend Pydantic schema field names exactly.
 *   - No runtime logic or default values.
 */

import type { RetrievalExplanationRead } from './chat';

// ─── Agent Registry ──────────────────────────────────────────────────────────

export interface AgentCapability {
  name: string;
  description: string;
}

export interface AgentRead {
  name: string;
  description: string;
  capabilities: AgentCapability[];
  is_active: boolean;
}

export interface AgentListResponse {
  agents: AgentRead[];
  total: number;
}

// ─── Workflow Plan ───────────────────────────────────────────────────────────

export type WorkflowStepStatus = 'pending' | 'running' | 'complete' | 'error';

export interface WorkflowStep {
  /** Normalized step index 1-6 */
  step: number;
  agent: string;
  status: WorkflowStepStatus;
  /** Duration in milliseconds */
  duration_ms: number | null;
  /** Memory entries used in this step */
  memory_count: number;
  /** Citations produced by this step */
  citations_count: number;
  /** Human-readable description of what occurred */
  description: string;
}

export interface WorkflowPlanStep {
  step: number;
  agent: string;
  description: string;
  estimated_duration_ms: number | null;
}

export interface WorkflowPlanPreviewResponse {
  question: string;
  selected_agents: string[];
  steps: WorkflowPlanStep[];
  estimated_total_ms: number | null;
}

// ─── Workflow Run ────────────────────────────────────────────────────────────

export interface WorkflowRunRequest {
  organization_id: string;
  question: string;
  agents?: string[];
  use_hybrid?: boolean;
}

export interface WorkflowRunResponse {
  answer: string;
  provider_used: string;
  participating_agents: string[];
  steps: WorkflowStep[];
  total_duration_ms: number | null;
  explanation: RetrievalExplanationRead | null;
  suggested_actions: string[];
}

// ─── Repository Agent ────────────────────────────────────────────────────────

export interface RepositorySearchRequest {
  organization_id: string;
  question: string;
  branch?: string;
  file_path?: string;
}

export interface CommitSummary {
  sha: string;
  message: string;
  author: string;
  date: string;
  files_changed: number;
}

export interface RepositorySearchResponse {
  answer: string;
  branch: string;
  commits: CommitSummary[];
  provider_used: string;
  explanation: RetrievalExplanationRead | null;
  suggested_actions: string[];
}

export interface BranchListResponse {
  branches: string[];
}

export interface FileHistoryRequest {
  organization_id: string;
  file_path: string;
  branch?: string;
}

export interface FileHistoryResponse {
  file_path: string;
  branch: string;
  commits: CommitSummary[];
}

// ─── Debug Agent ─────────────────────────────────────────────────────────────

export interface DebugAnalyzeRequest {
  organization_id: string;
  error_message: string;
  stack_trace?: string;
}

export interface IncidentMatch {
  memory_id: string;
  title: string | null;
  similarity: number;
  resolution: string | null;
}

export interface DebugAnalyzeResponse {
  analysis: string;
  incidents_found: IncidentMatch[];
  suggested_actions: string[];
  provider_used: string;
  explanation: RetrievalExplanationRead | null;
}

// ─── Client-side workflow history turn ───────────────────────────────────────

export type AgentPanelTab = 'registry' | 'workflow' | 'repository' | 'debug';

export interface WorkflowHistoryTurn {
  id: string;
  question: string;
  response: WorkflowRunResponse;
  created_at: string;
}
