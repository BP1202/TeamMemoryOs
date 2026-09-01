/**
 * Memory and Scenario types.
 * Field names mirror backend Pydantic schema field names exactly.
 *
 * Backend refs:
 *   - schemas/memory_entry.py → MemoryEntryRead / MemoryEntryCreate
 *   - schemas/scenario.py     → ScenarioRead / ScenarioCreate
 *   - models/memory_entry.py  → MemoryType enum (lowercase values)
 */

// ─── Memory Type ───────────────────────────────────────────────────────────
// Must match backend MemoryType enum (models/memory_entry.py) exactly.

export type MemoryType =
  | 'decision'
  | 'context'
  | 'artifact'
  | 'insight'
  | 'discussion';

export const MEMORY_TYPES: MemoryType[] = [
  'decision',
  'context',
  'artifact',
  'insight',
  'discussion',
];

export const MEMORY_TYPE_LABELS: Record<MemoryType, string> = {
  decision:    'Decision',
  context:     'Context',
  artifact:    'Artifact',
  insight:     'Insight',
  discussion:  'Discussion',
};

// ─── Memory Entry ──────────────────────────────────────────────────────────

export interface MemoryEntry {
  id: string;
  organization_id: string;
  scenario_id: string | null;
  created_by_user_id: string | null;
  memory_type: MemoryType;
  title: string | null;
  content: string;
  meta: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface MemoryEntryCreate {
  organization_id: string;
  memory_type: MemoryType;
  title?: string;
  content: string;
  meta?: Record<string, unknown>;
  scenario_id?: string;
}

// ─── Scenario ──────────────────────────────────────────────────────────────

export interface Scenario {
  id: string;
  organization_id: string;
  created_by_user_id: string | null;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScenarioCreate {
  organization_id: string;
  name: string;
  description?: string;
  is_active?: boolean;
}

// ─── Search ────────────────────────────────────────────────────────────────

export interface MemorySearchRequest {
  query_embedding: number[];
  organization_id: string;
  scenario_id?: string;
  top_k?: number;
}

export interface MemorySearchResult {
  entry: MemoryEntry;
  rank: number;
}

// ─── UI filter state (client only) ────────────────────────────────────────

export interface MemoryFilters {
  memoryType: MemoryType | 'all';
  scenarioId: string | 'all';
  search: string;
}
