/**
 * Auth store — JWT token, user, organization_id.
 * Persisted to localStorage.
 *
 * Rules:
 *   - Never store API response lists here.
 *   - Token is never logged.
 *   - org_id is read by the Axios interceptor — never from URL params.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@typedefs/auth';

interface AuthStore {
  token: string | null;
  user: User | null;
  organization_id: string | null;
  isAuthenticated: boolean;

  // Actions
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      organization_id: null,
      isAuthenticated: false,

      setAuth: (token, user) =>
        set({
          token,
          user,
          organization_id: user.organization_id,
          isAuthenticated: true,
        }),

      clearAuth: () =>
        set({
          token: null,
          user: null,
          organization_id: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'tmemos-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        organization_id: state.organization_id,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
