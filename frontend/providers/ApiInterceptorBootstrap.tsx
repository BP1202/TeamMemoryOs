/**
 * Auth interceptor bootstrapper.
 * Registers the Axios interceptors once when the app mounts.
 * Must be inside Router context (uses `navigate` for 401 redirect).
 */

import { useEffect, type ReactNode } from 'react';
import { useAuthStore } from '@stores/authStore';
import { registerAuthInterceptor } from '@lib/api/auth';
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
    registerErrorInterceptor(clearAuth, navigate);
  }, [clearAuth, navigate]);

  return <>{children}</>;
}
