/**
 * Agents service — wraps all agent-related API endpoints.
 *
 * Endpoints covered:
 *   GET  /api/v1/agents/
 *   GET  /api/v1/agents/{name}
 *   POST /api/v1/agents/workflow/plan
 *   POST /api/v1/agents/workflow/run
 *   POST /api/v1/agents/repository/search
 *   GET  /api/v1/agents/repository/branches
 *   POST /api/v1/agents/repository/file-history
 *   POST /api/v1/agents/debug/analyze
 *
 * Rules:
 *   - Only this file calls the agent endpoints.
 *   - No components or stores import from axios directly.
 *   - AbortController signal passed for cancellation support.
 *   - Normalized WorkflowStep[] shape isolates timeline from backend changes.
 */

import { apiClient } from '@lib/api/client';
import type {
  AgentListResponse,
  AgentRead,
  WorkflowPlanPreviewResponse,
  WorkflowRunRequest,
  WorkflowRunResponse,
  RepositorySearchRequest,
  RepositorySearchResponse,
  BranchListResponse,
  FileHistoryRequest,
  FileHistoryResponse,
  DebugAnalyzeRequest,
  DebugAnalyzeResponse,
} from '@typedefs/agents';

// ─── Agent Registry ──────────────────────────────────────────────────────────

export async function listAgents(signal?: AbortSignal): Promise<AgentListResponse> {
  const response = await apiClient.get<AgentListResponse>('/api/v1/agents/', { signal });
  return response.data;
}

export async function getAgent(name: string, signal?: AbortSignal): Promise<AgentRead> {
  const response = await apiClient.get<AgentRead>(`/api/v1/agents/${encodeURIComponent(name)}`, {
    signal,
  });
  return response.data;
}

// ─── Workflow ─────────────────────────────────────────────────────────────────

export interface WorkflowPlanRequest {
  organization_id: string;
  question: string;
  agents?: string[];
}

export async function planWorkflow(
  request: WorkflowPlanRequest,
  signal?: AbortSignal,
): Promise<WorkflowPlanPreviewResponse> {
  const response = await apiClient.post<WorkflowPlanPreviewResponse>(
    '/api/v1/agents/workflow/plan',
    request,
    { signal },
  );
  return response.data;
}

export async function runWorkflow(
  request: WorkflowRunRequest,
  signal?: AbortSignal,
): Promise<WorkflowRunResponse> {
  const response = await apiClient.post<WorkflowRunResponse>(
    '/api/v1/agents/workflow/run',
    request,
    { signal },
  );
  return response.data;
}

// ─── Repository Agent ────────────────────────────────────────────────────────

export async function searchRepository(
  request: RepositorySearchRequest,
  signal?: AbortSignal,
): Promise<RepositorySearchResponse> {
  const response = await apiClient.post<RepositorySearchResponse>(
    '/api/v1/agents/repository/search',
    request,
    { signal },
  );
  return response.data;
}

export async function listBranches(signal?: AbortSignal): Promise<BranchListResponse> {
  const response = await apiClient.get<BranchListResponse>(
    '/api/v1/agents/repository/branches',
    { signal },
  );
  return response.data;
}

export async function getFileHistory(
  request: FileHistoryRequest,
  signal?: AbortSignal,
): Promise<FileHistoryResponse> {
  const response = await apiClient.post<FileHistoryResponse>(
    '/api/v1/agents/repository/file-history',
    request,
    { signal },
  );
  return response.data;
}

// ─── Debug Agent ──────────────────────────────────────────────────────────────

export async function analyzeDebug(
  request: DebugAnalyzeRequest,
  signal?: AbortSignal,
): Promise<DebugAnalyzeResponse> {
  const response = await apiClient.post<DebugAnalyzeResponse>(
    '/api/v1/agents/debug/analyze',
    request,
    { signal },
  );
  return response.data;
}
