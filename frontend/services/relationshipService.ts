/**
 * Relationship service — relationship API endpoints.
 *
 * Endpoints:
 *   GET /api/v1/relationships/{id}                              → get by id
 *   GET /api/v1/relationships/entity/{id}/outgoing              → outgoing edges
 *   GET /api/v1/relationships/entity/{id}/neighbors             → all neighbors
 */

import { apiClient } from '@lib/api/client';
import type { Relationship, RelationshipType, Neighbor } from '@typedefs/graph';

// ─── Get single relationship ───────────────────────────────────────────────

export async function getRelationship(id: string): Promise<Relationship> {
  const { data } = await apiClient.get<Relationship>(
    `/api/v1/relationships/${id}`,
  );
  return data;
}

// ─── List outgoing relationships for entity ────────────────────────────────

export async function listOutgoingRelationships(
  entityId: string,
  params: {
    relationship_type?: RelationshipType;
    skip?: number;
    limit?: number;
  } = {},
): Promise<Relationship[]> {
  const { data } = await apiClient.get<Relationship[]>(
    `/api/v1/relationships/entity/${entityId}/outgoing`,
    {
      params: {
        skip:              params.skip  ?? 0,
        limit:             params.limit ?? 100,
        relationship_type: params.relationship_type,
      },
    },
  );
  return data;
}

// ─── List all neighbors for entity ────────────────────────────────────────

export async function listNeighbors(
  entityId: string,
  organizationId: string,
  params: { relationship_type?: RelationshipType } = {},
): Promise<Neighbor[]> {
  const { data } = await apiClient.get<Neighbor[]>(
    `/api/v1/relationships/entity/${entityId}/neighbors`,
    {
      params: {
        organization_id:   organizationId,
        relationship_type: params.relationship_type,
      },
    },
  );
  return data;
}
