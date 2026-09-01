/**
 * Organization ID request interceptor.
 * The backend does not require X-Organization-ID in Sprint 8.1 —
 * organization scope is resolved from the JWT token server-side.
 * This file is a no-op stub kept for future multi-org support.
 */

import { apiClient } from './client';

let getOrganizationId: (() => string | null) | null = null;

export function registerOrganizationInterceptor(
  orgIdGetter: () => string | null,
): void {
  getOrganizationId = orgIdGetter;

  apiClient.interceptors.request.use((config) => {
    const orgId = getOrganizationId?.();
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId;
    }
    return config;
  });
}
