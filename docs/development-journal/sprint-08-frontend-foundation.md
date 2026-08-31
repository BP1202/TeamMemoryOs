# Sprint 8.0 — Frontend Foundation & Workspace Shell

**Branch:** `feat/frontend-ai-workspace`
**Date:** 2025-01-08

---

## Entry 01 — Frontend Foundation Bootstrap

**Task:** Implement Sprint 8.0 — React 19 + Vite + TypeScript project setup, design system integration, global providers, router, Axios client, Zustand stores, AppShell, and UI primitives.

**Problem:** No frontend implementation existed. Config, design tokens, icons, and CSS variables were pre-authored but no entry point, package.json, components, stores, providers, layouts, router, or tests existed.

**Solution:**

### Infrastructure
- `package.json` with React 19, Vite 6, TypeScript 5.7, Tailwind 3, React Query 5, Zustand 5, Framer Motion 11, Radix UI (Dialog, Tooltip, Slot), Lucide React, react-hook-form 7, Axios 1.7, MSW 2, Vitest 2, RTL 16.
- `vite.config.ts` with full `@alias` path mapping for all folders.
- `tsconfig.json` with strict mode, path aliases (`@typedefs` to avoid TypeScript's reserved `@types` namespace).
- `vitest.config.ts` with jsdom environment and alias mirror.

### Design System Integration
- `styles/globals.css` — imports `tokens.css` before Tailwind directives, base layer reset, scrollbar, focus ring, reduced-motion override.
- Tailwind config already consumed from `design-tokens.ts`. No modifications needed.

### API Layer (`lib/api/`)
- `client.ts` — single Axios instance. Only place `axios.create` is called.
- `auth.ts` — JWT interceptor: injects `Authorization: Bearer <token>` from auth store.
- `organization.ts` — `X-Organization-ID` interceptor from auth store.
- `errors.ts` — global 401 handler (clears auth, redirects to `/login`), `normalizeError` for typed `ApiError`.

### Type System (`types/`)
- `api.ts` — `ApiError`, `PaginatedResponse`, `MemoryType`, `EntityType`, `RetrievalMode`, `ExplainabilityPayload`, `Citation`.
- `auth.ts` — `User`, `UserRole`, `LoginRequest`, `LoginResponse`, `AuthState`.
- `ui.ts` — `Theme`, `NavItem`, `UIState`, component variant types.

### State Management (`stores/`)
- `authStore.ts` — Zustand persist: token, user, organization_id, isAuthenticated. `setAuth` / `clearAuth`.
- `uiStore.ts` — Zustand persist: theme, sidebarCollapsed. `setTheme` / `toggleSidebar`.

### Configuration (`config/`)
- `constants.ts` — `APP_NAME`, `API_BASE_URL`, `DEBOUNCE_MS`, `DEFAULT_PAGE_SIZE`, stale times, feature flags.
- `navigation.ts` — `primaryNav` / `bottomNav` config arrays keyed to `NavIcons`.
- `queryClient.ts` — `QueryClient` singleton with default stale/gc times.

### Providers (`providers/`)
- `QueryProvider` — React Query + DevTools (dev only).
- `ThemeProvider` — applies dark/light/system class to `<html>`.
- `MotionProvider` — `LazyMotion` + `domAnimation` for Framer Motion.
- `TooltipProvider` — Radix global tooltip with 400ms delay.
- `ApiInterceptorBootstrap` — registers all Axios interceptors once on mount.
- `RootProvider` — composes all providers in correct order.

### UI Primitives (`components/ui/`)
- `Button` — 4 variants × 4 sizes, loading spinner, disabled, aria-busy/aria-disabled.
- `Card` + `CardHeader/Title/Description/Content/Footer` — 3 variants.
- `Input` — label/id linked, error aria-describedby, hint, disabled.
- `Badge` — 5 variants (default/success/warning/danger/info).
- `Spinner` — role=status + aria-label, 3 sizes.
- `Skeleton` / `SkeletonText` / `SkeletonCard` — animate-pulse placeholders.
- `Dialog` — Radix Dialog, focus trap, ESC, aria-modal, aria-labelledby.

### Feedback Components (`components/feedback/`)
- `EmptyState` — icon, heading, description, optional action CTA. role=status.
- `ErrorState` — heading, message, onRetry button. role=alert + aria-live=assertive.
- `LoadingState` — full-container Spinner + label. aria-busy=true.

### Layouts (`layouts/`)
- `Sidebar` — animated collapse (Framer Motion `m.nav`), `NavIcons` registry, keyboard nav, `useReducedMotion`, sign-out button.
- `Topbar` — 56px header, page title, user avatar + email.
- `AppShell` — `Sidebar` + `Topbar` + `<main id="main-content">` with `Outlet`.
- `WorkspaceLayout`, `AuthLayout`, `RootLayout`, `ErrorLayout` (React Router `errorElement`).

### Router (`app/`)
- `AuthGuard` — redirects unauthenticated users to `/login`, preserves `from` in location state.
- `router.tsx` — `BrowserRouter`, lazy-loaded routes, `RouteSuspense` wrapper, `ApiInterceptorBootstrap` inside router context.

### Feature Pages
- `features/auth/LoginPage.tsx` — React Hook Form, field validation (required, email format, min length). Sprint 8.1 will wire to the auth service.
- `features/dashboard/DashboardPage.tsx` — Placeholder grid confirming routing + AppShell.

### Test Infrastructure
- `vitest.config.ts` — jsdom, setup file, alias mirror, coverage config.
- `tests/setup.ts` — `@testing-library/jest-dom`, MSW lifecycle (`beforeAll`/`afterEach`/`afterAll`).
- `tests/mocks/handlers.ts` — MSW handlers for `/api/v1/auth/login`, `/api/v1/auth/me`.
- `tests/mocks/server.ts` — `setupServer` for Node environment.
- `tests/utils/renderWithProviders.tsx` — custom `render` with QueryClient + MemoryRouter.

**Validation:**

| Check | Result |
|---|---|
| `tsc --noEmit` | ✅ 0 errors |
| `npm test` (vitest run) | ✅ 8 files, 33 tests, 0 failures |
| `vite build` | ✅ 0 errors, 0 warnings |

**Test Coverage:** Button (7), Input (6), Badge (3), Spinner (2), EmptyState (4), ErrorState (5), AuthGuard (2), LoginPage (4).

**Security:**
- JWT stored in localStorage (documented risk, accepted for SPA).
- Token never logged — clearAuth wipes state.
- No `dangerouslySetInnerHTML` anywhere.
- `org_id` injected by Axios interceptor — never from URL.
- All interactive elements accessible via keyboard.

**Accessibility:**
- All inputs: `<label htmlFor>`, `aria-describedby` for errors.
- Spinner: `role="status"` + `aria-label`.
- EmptyState: `role="status"`.
- ErrorState: `role="alert"` + `aria-live="assertive"`.
- Dialog: Radix focus trap, ESC, `aria-modal`, close button `aria-label`.
- Button: `aria-busy` when loading, `aria-disabled` when disabled.
- Sidebar: `aria-label="Main navigation"`, collapsed items get `aria-label`.
- Motion: `useReducedMotion()` in Sidebar, CSS `prefers-reduced-motion` override.

**Status:** ✅ Complete
