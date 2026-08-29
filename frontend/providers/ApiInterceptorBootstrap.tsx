/**
 * Auth interceptor bootstrapper.
 * Registers the Axios interceptors once when the app mounts.
 * Must be a child of the auth store (Zustand hydration happens synchronously).
 */

import { useEffect, type ReactNode } from 'react';
import { useAuthStore } from '@stores/authStore';
import { registerAuthInterceptor } from '@lib/api/auth';
import { registerOrganizationInterceptor } from '@lib/api/organization';
import { registerErrorInterceptor } from '@lib/api/errors';

let interceptorsRegistered = false;

interface Props {
  children: ReactNode;
  navigate: (path: string) => void;
}

export function ApiInterceptorBootstrap({ children, navigate }: Props) {
  const clearAuth = useAuthStore((s) => s.clearAuth);

  useEffect(() => {
    if (interceptorsRegistered) return;
    interceptorsRegistered = true;

    registerAuthInterceptor(() => useAuthStore.getState().token);
    registerOrganizationInterceptor(
      () => useAuthStore.getState().organization_id,
    );
    registerErrorInterceptor(clearAuth, navigate);
  }, [clearAuth, navigate]);

  return <>{children}</>;
}
