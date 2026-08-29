/**
 * Organization ID request interceptor.
 * Injects X-Organization-ID from the auth store into every outgoing request.
 * Never reads org_id from URL parameters.
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
