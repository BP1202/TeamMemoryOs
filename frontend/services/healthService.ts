/**
 * Health service — /api/v1/health
 *
 * GET /api/v1/health/   — backend liveness
 * GET /api/v1/health/db — database connectivity
 */

import { apiClient } from '@lib/api/client';
import type { DbHealthResponse, HealthResponse } from '@typedefs/api';

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/api/v1/health/');
  return data;
}

export async function getDbHealth(): Promise<DbHealthResponse> {
  const { data } = await apiClient.get<DbHealthResponse>('/api/v1/health/db');
  return data;
}
