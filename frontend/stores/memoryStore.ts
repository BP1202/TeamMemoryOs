/**
 * Memory workspace Zustand store.
 * Owns: drawer open/close state, selected memory ID, active filters.
 * Never owns: API response lists (those live in React Query).
 */

import { create } from 'zustand';
import type { MemoryFilters } from '@typedefs/memory';

interface MemoryStore {
  // Drawer state
  isDetailDrawerOpen: boolean;
  selectedMemoryId: string | null;
  isCreateDrawerOpen: boolean;

  // Active filters (client UI state only)
  filters: MemoryFilters;

  // Actions
  openDetailDrawer: (memoryId: string) => void;
  closeDetailDrawer: () => void;
  openCreateDrawer: () => void;
  closeCreateDrawer: () => void;
  setFilter: (patch: Partial<MemoryFilters>) => void;
  resetFilters: () => void;
}

const DEFAULT_FILTERS: MemoryFilters = {
  memoryType: 'all',
  scenarioId: 'all',
  search: '',
};

export const useMemoryStore = create<MemoryStore>((set) => ({
  isDetailDrawerOpen: false,
  selectedMemoryId: null,
  isCreateDrawerOpen: false,
  filters: DEFAULT_FILTERS,

  openDetailDrawer: (memoryId) =>
    set({ isDetailDrawerOpen: true, selectedMemoryId: memoryId }),

  closeDetailDrawer: () =>
    set({ isDetailDrawerOpen: false, selectedMemoryId: null }),

  openCreateDrawer: () => set({ isCreateDrawerOpen: true }),

  closeCreateDrawer: () => set({ isCreateDrawerOpen: false }),

  setFilter: (patch) =>
    set((state) => ({ filters: { ...state.filters, ...patch } })),

  resetFilters: () => set({ filters: DEFAULT_FILTERS }),
}));
