/**
 * Knowledge Graph Zustand store.
 *
 * Owns:
 *   - Selected entity ID (opens inspector drawer)
 *   - Set of expanded entity IDs (nodes whose neighbors have been loaded)
 *   - Graph filters (entity type, relationship type, search query)
 *
 * Never owns: API response lists (React Query owns those).
 */

import { create } from 'zustand';
import type { GraphFilters } from '@typedefs/graph';

interface GraphStore {
  // Inspector drawer
  selectedEntityId: string | null;
  isInspectorOpen: boolean;

  // Expanded neighbor nodes (stored as plain array to stay JSON-serializable)
  expandedEntityIds: string[];

  // Filters
  filters: GraphFilters;

  // Actions
  selectEntity: (id: string) => void;
  deselectEntity: () => void;
  expandEntity: (id: string) => void;
  collapseAll: () => void;
  setFilter: (patch: Partial<GraphFilters>) => void;
  resetFilters: () => void;
  resetGraph: () => void;
}

const DEFAULT_FILTERS: GraphFilters = {
  entityType:       'all',
  relationshipType: 'all',
  search:           '',
};

export const useGraphStore = create<GraphStore>()((set) => ({
  selectedEntityId:  null,
  isInspectorOpen:   false,
  expandedEntityIds: [],
  filters:           DEFAULT_FILTERS,

  selectEntity: (id) =>
    set({ selectedEntityId: id, isInspectorOpen: true }),

  deselectEntity: () =>
    set({ selectedEntityId: null, isInspectorOpen: false }),

  expandEntity: (id) =>
    set((state) => ({
      expandedEntityIds: state.expandedEntityIds.includes(id)
        ? state.expandedEntityIds
        : [...state.expandedEntityIds, id],
    })),

  collapseAll: () =>
    set({ expandedEntityIds: [] }),

  setFilter: (patch) =>
    set((state) => ({ filters: { ...state.filters, ...patch } })),

  resetFilters: () => set({ filters: DEFAULT_FILTERS }),

  resetGraph: () =>
    set({
      selectedEntityId:  null,
      isInspectorOpen:   false,
      expandedEntityIds: [],
      filters:           DEFAULT_FILTERS,
    }),
}));
