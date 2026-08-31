/**
 * JWT authentication request interceptor.
 * Injects the Bearer token from auth store into every outgoing request.
 * Never reads the token from a URL param or component prop.
 */

import { apiClient } from './client';

// Lazy import to avoid circular dependency — stores import from lib/api
let getToken: (() => string | null) | null = null;

export function registerAuthInterceptor(tokenGetter: () => string | null): void {
  getToken = tokenGetter;

  apiClient.interceptors.request.use((config) => {
    const token = getToken?.();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
}
