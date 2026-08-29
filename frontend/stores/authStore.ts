/**
 * Auth store — JWT token, user.
 * Persisted to localStorage.
 *
 * Rules:
 *   - Never store API response lists here.
 *   - Token is never logged.
 *   - org_id injected by the Axios interceptor from X-Organization-ID
 *     if needed by the backend — not from URL params.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@typedefs/auth';

interface AuthStore {
  token: string | null;
  user: User | null;
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
      isAuthenticated: false,

      setAuth: (token, user) =>
        set({
          token,
          user,
          isAuthenticated: true,
        }),

      clearAuth: () =>
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'tmemos-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
