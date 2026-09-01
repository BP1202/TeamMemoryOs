/**
 * Memory service — all memory entry API endpoints.
 *
 * Endpoints:
 *   GET  /api/v1/memory/organization/{orgId}  → list entries
 *   POST /api/v1/memory/                      → create entry
 *   GET  /api/v1/memory/{id}                  → get entry by id
 *   POST /api/v1/memory/search                → semantic search
 */

import { apiClient } from '@lib/api/client';
import type {
  MemoryEntry,
  MemoryEntryCreate,
  MemorySearchRequest,
  MemorySearchResult,
} from '@typedefs/memory';

// ─── List memories by org ─────────────────────────────────────────────────

export async function listMemoryEntries(
  organizationId: string,
  params: { skip?: number; limit?: number } = {},
): Promise<MemoryEntry[]> {
  const { data } = await apiClient.get<MemoryEntry[]>(
    `/api/v1/memory/organization/${organizationId}`,
    { params: { skip: params.skip ?? 0, limit: params.limit ?? 100 } },
  );
  return data;
}

// ─── Get single memory entry ──────────────────────────────────────────────

export async function getMemoryEntry(id: string): Promise<MemoryEntry> {
  const { data } = await apiClient.get<MemoryEntry>(`/api/v1/memory/${id}`);
  return data;
}

// ─── Create memory entry ──────────────────────────────────────────────────

export async function createMemoryEntry(
  payload: MemoryEntryCreate,
): Promise<MemoryEntry> {
  const { data } = await apiClient.post<MemoryEntry>('/api/v1/memory/', payload);
  return data;
}

// ─── Semantic search ──────────────────────────────────────────────────────

export async function searchMemoryEntries(
  body: MemorySearchRequest,
): Promise<MemorySearchResult[]> {
  const { data } = await apiClient.post<MemorySearchResult[]>(
    '/api/v1/memory/search',
    body,
  );
  return data;
}
