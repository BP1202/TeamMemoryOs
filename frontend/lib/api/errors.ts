/**
 * Global API error handling.
 *
 * Rules:
 *   - 401 responses clear the auth store and redirect to /login.
 *   - All errors are normalized to typed ApiError before reaching feature code.
 *   - Token is NEVER logged.
 */

import { AxiosError } from 'axios';
import { apiClient } from './client';
import type { ApiError } from '@typedefs/api';

type AuthClearer = () => void;
type Redirector = (path: string) => void;

export function registerErrorInterceptor(
  clearAuth: AuthClearer,
  redirect: Redirector,
): void {
  apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        clearAuth();
        redirect('/login');
      }

      return Promise.reject(normalizeError(error));
    },
  );
}

export function normalizeError(error: unknown): ApiError {
  if (error instanceof AxiosError && error.response) {
    const data = error.response.data as Record<string, unknown> | undefined;
    return {
      status:  error.response.status,
      code:    (data?.code as string) ?? 'API_ERROR',
      message: (data?.detail as string) ?? (data?.message as string) ?? error.message,
      details: data as Record<string, unknown> | undefined,
    };
  }

  if (error instanceof Error) {
    return {
      status:  0,
      code:    'NETWORK_ERROR',
      message: error.message,
    };
  }

  return {
    status:  0,
    code:    'UNKNOWN_ERROR',
    message: 'An unexpected error occurred.',
  };
}
