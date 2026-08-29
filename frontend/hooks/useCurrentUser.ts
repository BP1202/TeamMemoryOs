/**
 * useCurrentUser — fetches and caches the authenticated user profile.
 *
 * Enabled only when a token exists in the auth store.
 * On success, hydrates the auth store user field.
 */

import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { getCurrentUser } from '@services/userService';
import { useAuthStore } from '@stores/authStore';
import { STALE_TIME_USER } from '@config/constants';

export const CURRENT_USER_KEY = ['currentUser'] as const;

export function useCurrentUser() {
  const token    = useAuthStore((s) => s.token);
  const setAuth  = useAuthStore((s) => s.setAuth);
  const user     = useAuthStore((s) => s.user);

  const query = useQuery({
    queryKey: CURRENT_USER_KEY,
    queryFn:  getCurrentUser,
    enabled:  !!token,
    staleTime: STALE_TIME_USER,
    retry: 1,
  });

  // Hydrate auth store whenever the profile is (re)fetched
  useEffect(() => {
    if (query.data && token) {
      setAuth(token, query.data);
    }
  }, [query.data, token, setAuth]);

  return {
    user:      user ?? query.data ?? null,
    isLoading: query.isLoading,
    isError:   query.isError,
    error:     query.error,
    refetch:   query.refetch,
  };
}
