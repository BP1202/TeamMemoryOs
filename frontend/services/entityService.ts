/**
 * Entity service — entity API endpoints.
 *
 * Endpoints:
 *   GET /api/v1/entities/organization/{orgId}    → list entities
 *   GET /api/v1/entities/{id}                    → get entity by id
 *   GET /api/v1/entities/memory/{memoryId}       → get entities for memory
 */

import { apiClient } from '@lib/api/client';
import type { Entity, EntityType } from '@typedefs/graph';

// ─── List entities by org ──────────────────────────────────────────────────

export async function listEntities(
  organizationId: string,
  params: { entity_type?: EntityType; skip?: number; limit?: number } = {},
): Promise<Entity[]> {
  const { data } = await apiClient.get<Entity[]>(
    `/api/v1/entities/organization/${organizationId}`,
    {
      params: {
        skip:        params.skip  ?? 0,
        limit:       params.limit ?? 200,
        entity_type: params.entity_type,
      },
    },
  );
  return data;
}

// ─── Get single entity ────────────────────────────────────────────────────

export async function getEntity(id: string): Promise<Entity> {
  const { data } = await apiClient.get<Entity>(`/api/v1/entities/${id}`);
  return data;
}

// ─── Get entities for memory entry ────────────────────────────────────────

export async function getEntitiesForMemory(
  memoryEntryId: string,
): Promise<Entity[]> {
  const { data } = await apiClient.get<Entity[]>(
    `/api/v1/entities/memory/${memoryEntryId}`,
  );
  return data;
}
