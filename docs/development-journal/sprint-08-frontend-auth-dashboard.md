# Sprint 8.1 — Authentication & Dashboard

**Branch:** `feat/frontend-ai-workspace`
**Date:** 2025-01-08

---

## Entry 02 — Authentication & Dashboard Implementation

**Task:** Implement full authentication flow (login, session persistence, logout, 401 handling) and Dashboard page (health widgets, stat counters, quick actions grid, ErrorBoundary, CommandPalette).

**Problem:** Sprint 8.0 left LoginPage as a stub with no API integration and DashboardPage as a static placeholder. No service layer, no hooks, no real data flow existed.

**Solution:**

### Type Corrections
- `types/auth.ts` — Corrected `User` to mirror `UserRead` schema: removed `role`/`organization_id` (not in backend schema), added `updated_at`. Corrected `LoginRequest` to use `username` (OAuth2 convention). `LoginResponse` now has no `user` field — profile fetched via `/users/me`.
- `types/api.ts` — Added `HealthResponse`, `DbHealthResponse`, `DashboardStats`.
- `stores/authStore.ts` — Removed `organization_id` from store (User schema has no org_id).

### Services Layer (`services/`)
- `authService.ts` — `loginUser()`: POST `/api/v1/auth/login` as `application/x-www-form-urlencoded` (OAuth2PasswordRequestForm).
- `userService.ts` — `getCurrentUser()`: GET `/api/v1/users/me`.
- `healthService.ts` — `getHealth()`, `getDbHealth()` for health endpoints.
- `dashboardService.ts` — `getMemoryList()`, `getScenarioList()`, `getAgentList()` for dashboard counts.

### Hooks (`hooks/`)
- `useCurrentUser.ts` — `useQuery` for authenticated user. Hydrates auth store on success. Enabled only when token exists.
- `useLogout.ts` — Clears auth store, clears React Query cache, navigates to `/login`.

### LoginPage (Full Integration)
- `useMutation` wired to `loginUser` → on success: fetches user profile, sets auth store, seeds query cache, navigates to `from`.
- On 401: shows field-level "Invalid email or password" error on password field.
- On 500+: shows root-level error alert (`role="alert"`).
- Button shows `isLoading` during mutation.

### ErrorBoundary (`components/feedback/ErrorBoundary.tsx`)
- React class-based boundary. `role="alert"` + `aria-live="assertive"`. Custom fallback prop. Reset button clears boundary state.
- Mounted in `router.tsx` wrapping all workspace routes.

### CommandPalette (`components/CommandPalette.tsx`)
- Ctrl+K / Cmd+K opens Radix Dialog. ESC closes (Radix built-in).
- `aria-modal`, focus trap, `aria-label="Search"` on input.
- `.sr-only` DialogTitle for screen readers.
- Search logic deferred to Sprint 8.4.
- Mounted globally in `AppRouter` inside router context.

### Dashboard Widgets
- `HealthWidget` — two-row status display (backend + db). Skeleton loading. Success badges. Error badge on failure. `role="status"` + `aria-busy`.
- `StatWidget` — numeric metric card. Skeleton on load. "Unavailable" on error. `role="status"`.
- `QuickActionsGrid` — four workspace cards (Memory, Graph, Chat, Agents). `role="list"` + `role="listitem"`. Links enabled when `available: true`.
- `DashboardPage` — three `useQuery` calls for memory/scenario/agent counts. Personalized greeting from auth store user.

### Router Updates
- `ErrorBoundary` wraps workspace routes.
- `CommandPalette` mounted at root inside `ApiInterceptorBootstrap`.
- `BrowserRouter` has `future: { v7_startTransition, v7_relativeSplatPath }` to silence v7 migration warnings.

### Sidebar
- `useLogout` hook used instead of raw `clearAuth` — ensures query cache is cleared on sign out.

**Validation:**

| Check | Result |
|---|---|
| `tsc --noEmit` | ✅ 0 errors |
| `vitest run` | ✅ 14 files, 62 tests, 0 failures |
| `vite build` | ✅ 0 errors, 0 warnings |

**Test Coverage added (Sprint 8.1):**

| Suite | Tests |
|---|---|
| `LoginPage` | 7 (renders×2, validation×2, success×1, failure×2) |
| `HealthWidget` | 3 (loading, healthy, error) |
| `StatWidget` | 5 (label, value, loading, error, a11y) |
| `DashboardPage` | 6 (container, heading, loading widgets, data, health, quick actions) |
| `ErrorBoundary` | 5 (children, fallback, retry, custom fallback, aria) |
| `CommandPalette` | 5 (hidden, Ctrl+K, Cmd+K, title, toggle) |
| `useLogout` | 2 (clears auth, navigates) |

**Security:**
- Login uses `application/x-www-form-urlencoded` — credentials not in JSON body.
- Token stored in localStorage, never logged, never in URL.
- 401 global interceptor: clears auth, redirects to `/login`.
- Authorization header injected by Axios interceptor only.
- No sensitive user data rendered in error messages.

**Accessibility:**
- `LoginPage`: `role="alert"` for root error, all inputs labeled, errors via `aria-describedby`.
- `ErrorBoundary`: `role="alert"` + `aria-live="assertive"`.
- `CommandPalette`: focus trap (Radix), `.sr-only` title, `aria-label` on search input, ESC close.
- `HealthWidget`/`StatWidget`: `role="status"` + `aria-busy`, status never by color alone (text badge).
- `QuickActionsGrid`: `role="list"` / `role="listitem"`, disabled items have `aria-label` noting "coming soon".

**Status:** ✅ Complete

---

## Entry 03 — Memory Workspace (Sprint 8.2)

**Task:** Implement the complete Memory Workspace — paginated table, semantic search, Create Memory drawer, Memory Detail drawer, Scenario list with filters, Create Scenario dialog, and all loading/empty/error states.

**Branch:** `feat/frontend-ai-workspace`
**Date:** 2025-01-09

**Problem:** The `/memory` route did not exist. No memory or scenario services, types, store, or feature components existed. The backend MemoryType enum (lowercase: `decision`, `context`, `artifact`, `insight`, `discussion`) was also misaligned with the placeholder uppercase values in `types/api.ts`.

**Solution:**

### Types
- `types/memory.ts` (new) — `MemoryEntry`, `MemoryEntryCreate`, `Scenario`, `ScenarioCreate`, `MemorySearchRequest`, `MemorySearchResult`, `MemoryFilters`. `MemoryType` enum matches backend exactly (lowercase values).
- `types/api.ts` — Replaced inline uppercase `MemoryType` union with re-export from `types/memory.ts`.

### Services
- `services/memoryService.ts` (new) — `listMemoryEntries`, `getMemoryEntry`, `createMemoryEntry`, `searchMemoryEntries`.
- `services/scenarioService.ts` (new) — `listScenarios`, `createScenario`.
- `services/index.ts` — Updated barrel to export new service functions.

### Store
- `stores/memoryStore.ts` (new) — Zustand store for drawer state (`isDetailDrawerOpen`, `isCreateDrawerOpen`, `selectedMemoryId`) and client-side filters (`memoryType`, `scenarioId`, `search`). No API response data stored.

### UI Primitive
- `components/ui/Drawer.tsx` (new) — Slide-in drawer built on Radix UI Dialog. Full accessibility: focus trap, ESC, `aria-modal`, `aria-labelledby`, portal.
- `components/ui/index.ts` — Added Drawer exports.

### Feature Components
- `features/memory/MemoryTypeBadge.tsx` — Badge with icon for each MemoryType.
- `features/memory/MemoryTableSkeleton.tsx` — Skeleton loading rows for table.
- `features/memory/MemoryTable.tsx` — Keyboard-navigable table with row click → detail drawer.
- `features/memory/MemorySearchBar.tsx` — Debounced search input (300ms) with `role="search"`.
- `features/memory/MemoryDetailDrawer.tsx` — Drawer showing full memory detail with deep-link support (`/memory/:memoryId`).
- `features/memory/CreateMemoryDrawer.tsx` — React Hook Form drawer; validates required content; invalidates cache on success.
- `features/memory/ScenarioList.tsx` — Scenario filter chips from React Query; loading/error/empty states.
- `features/memory/CreateScenarioDialog.tsx` — Dialog form; validates name; invalidates scenario cache on success.
- `features/memory/MemoryPage.tsx` — Full page orchestration with client-side filter+search, all four states (loading/empty/filtered-empty/data).

### Router
- `app/router.tsx` — Added `/memory` and `/memory/:memoryId` lazy routes inside AuthGuard.

### Tests (MSW + Vitest + RTL)
- `tests/mocks/handlers.ts` — Added full MemoryEntry/Scenario fixture shapes and handlers for all 6 new endpoints (list, get, create, search, scenario list, create scenario).
- `features/memory/MemoryPage.test.tsx` — 24 tests: data state, loading, empty (two cases), error+retry, search, type filter, detail drawer open/close/content, create memory success/failure/validation, scenario dialog success/failure/validation, scenario filter.

**Validation:**
- `tsc --noEmit` → 0 errors
- `vitest run` → 86/86 tests pass (24 new)
- `vite build` → Clean production build, MemoryPage chunk 24.04 kB gzipped to 6.36 kB

**Security:** Memory content rendered as plain `whitespace-pre-wrap` text — never innerHTML. `org_id` from auth store only. IDs not exposed in URL for API calls.

**Accessibility:** Table `role="table"` + keyboard navigation (Enter/Space activates row). Drawer focus trap + ESC + `aria-modal`. Forms: all labels linked via `htmlFor`, errors via `aria-describedby`. Search `role="search"`. Scenario chips `aria-pressed`.

**Status:** ✅ Complete

