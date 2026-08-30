/**
 * Application router.
 * All feature routes are lazy-loaded.
 * AuthGuard wraps all workspace routes.
 * ErrorBoundary wraps all route trees.
 * CommandPalette is mounted globally in the workspace shell.
 */

import { lazy, Suspense } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from 'react-router-dom';

import { AuthGuard } from './AuthGuard';
import { WorkspaceLayout } from '@layouts/WorkspaceLayout';
import { AuthLayout } from '@layouts/AuthLayout';
import { RootLayout } from '@layouts/RootLayout';
import { ErrorLayout } from '@layouts/ErrorLayout';
import { ApiInterceptorBootstrap } from '@providers/ApiInterceptorBootstrap';
import { LoadingState } from '@components/feedback/LoadingState';
import { ErrorBoundary } from '@components/feedback/ErrorBoundary';
import { CommandPalette } from '@components/CommandPalette';

// ─── Lazy-loaded routes ───────────────────────────────────────────────────

const LoginPage     = lazy(() => import('@features/auth/LoginPage').then((m) => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import('@features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const MemoryPage    = lazy(() => import('@features/memory/MemoryPage').then((m) => ({ default: m.MemoryPage })));
const GraphPage     = lazy(() => import('@features/graph/GraphPage').then((m) => ({ default: m.GraphPage })));
const ChatPage      = lazy(() => import('@features/chat/ChatPage').then((m) => ({ default: m.ChatPage })));

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
      {/* CommandPalette mounted at root — available on all authenticated pages */}
      <CommandPalette />

      <Routes>
        <Route element={<RootLayout />} errorElement={<ErrorLayout />}>
          {/* Authenticated workspace */}
          <Route
            element={
              <AuthGuard>
                <ErrorBoundary>
                  <WorkspaceLayout />
                </ErrorBoundary>
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
            {/* Memory Workspace */}
            <Route
              path="/memory"
              element={
                <RouteSuspense>
                  <MemoryPage />
                </RouteSuspense>
              }
            />
            {/* Deep-link to a memory entry */}
            <Route
              path="/memory/:memoryId"
              element={
                <RouteSuspense>
                  <MemoryPage />
                </RouteSuspense>
              }
            />
            {/* Knowledge Graph Workspace */}
            <Route
              path="/graph"
              element={
                <RouteSuspense>
                  <GraphPage />
                </RouteSuspense>
              }
            />
            {/* AI Chat Workspace */}
            <Route
              path="/chat"
              element={
                <RouteSuspense>
                  <ChatPage />
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
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <InnerRouter />
    </BrowserRouter>
  );
}
