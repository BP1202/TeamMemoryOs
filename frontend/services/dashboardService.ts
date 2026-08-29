/**
 * Dashboard service — aggregated data for the Dashboard widgets.
 *
 * Memory count:   GET /api/v1/memory/organization/{org_id}?limit=1
 * Scenario count: GET /api/v1/scenarios/organization/{org_id}?limit=1
 * Agent count:    GET /api/v1/agents/
 *
 * Note: The backend does not expose a dedicated count endpoint.
 * We fetch with limit=1 and read the full list for agents (small, bounded set).
 */

import { apiClient } from '@lib/api/client';

export interface MemoryListItem {
  id: string;
}

export interface ScenarioListItem {
  id: string;
}

export interface AgentListResponse {
  agents: { name: string }[];
  total: number;
}

export async function getMemoryList(organizationId: string): Promise<MemoryListItem[]> {
  const { data } = await apiClient.get<MemoryListItem[]>(
    `/api/v1/memory/organization/${organizationId}`,
    { params: { skip: 0, limit: 100 } },
  );
  return data;
}

export async function getScenarioList(organizationId: string): Promise<ScenarioListItem[]> {
  const { data } = await apiClient.get<ScenarioListItem[]>(
    `/api/v1/scenarios/organization/${organizationId}`,
    { params: { skip: 0, limit: 100 } },
  );
  return data;
}

export async function getAgentList(): Promise<AgentListResponse> {
  const { data } = await apiClient.get<AgentListResponse>('/api/v1/agents/');
  return data;
}
