/**
 * lib/api barrel export.
 */

export { apiClient } from './client';
export { registerAuthInterceptor } from './auth';
export { registerOrganizationInterceptor } from './organization';
export { registerErrorInterceptor, normalizeError } from './errors';
