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
export type UserRole = 'Owner' | 'Tech Lead' | 'Developer' | 'Security Auditor';

interface UIStore {
  theme: Theme;
  sidebarCollapsed: boolean;
  currentRole: UserRole;
  currentWorkspace: string;
  showOnboardingModal: boolean;
  showGuidedDemoModal: boolean;
  guidedDemoStep: number;

  // Actions
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentRole: (role: UserRole) => void;
  setCurrentWorkspace: (workspace: string) => void;
  setShowOnboardingModal: (show: boolean) => void;
  setShowGuidedDemoModal: (show: boolean) => void;
  setGuidedDemoStep: (step: number) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarCollapsed: false,
      currentRole: 'Owner',
      currentWorkspace: 'SunBots Technologies',
      showOnboardingModal: false,
      showGuidedDemoModal: false,
      guidedDemoStep: 0,

      setTheme: (theme) => set({ theme }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setCurrentRole: (currentRole) => set({ currentRole }),
      setCurrentWorkspace: (currentWorkspace) => set({ currentWorkspace }),
      setShowOnboardingModal: (showOnboardingModal) => set({ showOnboardingModal }),
      setShowGuidedDemoModal: (showGuidedDemoModal) => set({ showGuidedDemoModal }),
      setGuidedDemoStep: (guidedDemoStep) => set({ guidedDemoStep }),
    }),
    {
      name: 'tmemos-ui',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        currentRole: state.currentRole,
        currentWorkspace: state.currentWorkspace,
      }),
    },
  ),
);

