/**
 * UI store — theme, sidebar state, client-only UI flags.
 *
 * Rules:
 *   - Never store server data here.
 *   - Never store loading/error states here.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Theme } from '@typedefs/ui';

interface UIStore {
  theme: Theme;
  sidebarCollapsed: boolean;

  // Actions
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarCollapsed: false,

      setTheme: (theme) => set({ theme }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'tmemos-ui',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    },
  ),
);
