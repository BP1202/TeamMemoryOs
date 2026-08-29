/**
 * useLogout — clears auth state, React Query cache, and redirects to /login.
 */

import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@stores/authStore';

export function useLogout() {
  const clearAuth   = useAuthStore((s) => s.clearAuth);
  const navigate    = useNavigate();
  const queryClient = useQueryClient();

  return useCallback(() => {
    clearAuth();
    queryClient.clear();
    navigate('/login', { replace: true });
  }, [clearAuth, navigate, queryClient]);
}
