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

import { LoginPage } from '@features/auth/LoginPage';
import { OnboardingModal } from '@features/onboarding/OnboardingModal';
import { GuidedDemoModal } from '@components/GuidedDemoModal';

// ─── Lazy-loaded routes ───────────────────────────────────────────────────

const DashboardPage        = lazy(() => import('@features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const KnowledgePage        = lazy(() => import('@features/memory/KnowledgePage').then((m) => ({ default: m.KnowledgePage })));
const ChatPage             = lazy(() => import('@features/chat/ChatPage').then((m) => ({ default: m.ChatPage })));
const IncidentPRCenterPage = lazy(() => import('@features/incidents/IncidentPRCenterPage').then((m) => ({ default: m.IncidentPRCenterPage })));
const WorkspacePage        = lazy(() => import('@features/workspace/WorkspacePage').then((m) => ({ default: m.WorkspacePage })));
const NotFoundPage         = lazy(() => import('@features/NotFoundPage').then((m) => ({ default: m.NotFoundPage })));

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
      {/* CommandPalette, OnboardingModal & GuidedDemoModal mounted at root */}
      <CommandPalette />
      <OnboardingModal />
      <GuidedDemoModal />

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
            {/* 1. 🏠 Home */}
            <Route
              index
              element={
                <RouteSuspense>
                  <DashboardPage />
                </RouteSuspense>
              }
            />

            {/* 2. 🤖 AI Assistant */}
            <Route
              path="/chat"
              element={
                <RouteSuspense>
                  <ChatPage />
                </RouteSuspense>
              }
            />

            {/* 3. 🧠 Team Knowledge (Timeline + Graph) */}
            <Route
              path="/knowledge"
              element={
                <RouteSuspense>
                  <KnowledgePage />
                </RouteSuspense>
              }
            />
            <Route
              path="/memory"
              element={
                <RouteSuspense>
                  <KnowledgePage />
                </RouteSuspense>
              }
            />
            <Route
              path="/memory/:memoryId"
              element={
                <RouteSuspense>
                  <KnowledgePage />
                </RouteSuspense>
              }
            />
            <Route
              path="/graph"
              element={
                <RouteSuspense>
                  <KnowledgePage />
                </RouteSuspense>
              }
            />

            {/* 4. 🚨 Incident & PR Defense Center */}
            <Route
              path="/incidents"
              element={
                <RouteSuspense>
                  <IncidentPRCenterPage />
                </RouteSuspense>
              }
            />
            <Route
              path="/guardian"
              element={
                <RouteSuspense>
                  <IncidentPRCenterPage />
                </RouteSuspense>
              }
            />

            {/* 5. ⚙️ Workspace & Governance */}
            <Route
              path="/workspace"
              element={
                <RouteSuspense>
                  <WorkspacePage />
                </RouteSuspense>
              }
            />
            <Route
              path="/settings"
              element={
                <RouteSuspense>
                  <WorkspacePage />
                </RouteSuspense>
              }
            />
            <Route
              path="/agents"
              element={
                <RouteSuspense>
                  <WorkspacePage />
                </RouteSuspense>
              }
            />
          </Route>


          {/* Auth (unauthenticated) */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
          </Route>

          {/* 404 — global NotFound */}
          <Route
            path="*"
            element={
              <RouteSuspense>
                <NotFoundPage />
              </RouteSuspense>
            }
          />
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
