/**
 * Application router.
 * All feature routes are lazy-loaded.
 * AuthGuard wraps all workspace routes.
 */

import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

import { AuthGuard } from './AuthGuard';
import { WorkspaceLayout } from '@layouts/WorkspaceLayout';
import { AuthLayout } from '@layouts/AuthLayout';
import { RootLayout } from '@layouts/RootLayout';
import { ErrorLayout } from '@layouts/ErrorLayout';
import { ApiInterceptorBootstrap } from '@providers/ApiInterceptorBootstrap';
import { LoadingState } from '@components/feedback/LoadingState';

// ─── Lazy-loaded routes ───────────────────────────────────────────────────

const LoginPage     = lazy(() => import('@features/auth/LoginPage').then((m) => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import('@features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })));

// ─── Route fallback ───────────────────────────────────────────────────────

function RouteSuspense({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<LoadingState label="Loading page…" />}>
      {children}
    </Suspense>
  );
}

// ─── Inner router (has access to navigate) ───────────────────────────────

function InnerRouter() {
  const navigate = useNavigate();

  return (
    <ApiInterceptorBootstrap navigate={navigate}>
      <Routes>
        <Route element={<RootLayout />} errorElement={<ErrorLayout />}>
          {/* Authenticated workspace */}
          <Route
            element={
              <AuthGuard>
                <WorkspaceLayout />
              </AuthGuard>
            }
          >
            <Route
              index
              element={
                <RouteSuspense>
                  <DashboardPage />
                </RouteSuspense>
              }
            />
          </Route>

          {/* Auth (unauthenticated) */}
          <Route element={<AuthLayout />}>
            <Route
              path="/login"
              element={
                <RouteSuspense>
                  <LoginPage />
                </RouteSuspense>
              }
            />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ApiInterceptorBootstrap>
  );
}

// ─── Exported router ──────────────────────────────────────────────────────

export function AppRouter() {
  return (
    <BrowserRouter>
      <InnerRouter />
    </BrowserRouter>
  );
}
