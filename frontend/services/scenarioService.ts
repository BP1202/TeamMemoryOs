/**
 * Scenario service — scenario API endpoints.
 *
 * Endpoints:
 *   GET  /api/v1/scenarios/organization/{orgId}  → list scenarios
 *   POST /api/v1/scenarios/                      → create scenario
 */

import { apiClient } from '@lib/api/client';
import type { Scenario, ScenarioCreate } from '@typedefs/memory';

// ─── List scenarios by org ─────────────────────────────────────────────────

export async function listScenarios(
  organizationId: string,
  params: { skip?: number; limit?: number } = {},
): Promise<Scenario[]> {
  const { data } = await apiClient.get<Scenario[]>(
    `/api/v1/scenarios/organization/${organizationId}`,
    { params: { skip: params.skip ?? 0, limit: params.limit ?? 100 } },
  );
  return data;
}

// ─── Create scenario ───────────────────────────────────────────────────────

export async function createScenario(
  payload: ScenarioCreate,
): Promise<Scenario> {
  const { data } = await apiClient.post<Scenario>('/api/v1/scenarios/', payload);
  return data;
}
