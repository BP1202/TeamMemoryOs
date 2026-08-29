# Sprint 8 — Frontend AI Workspace: Final Implementation Blueprint

## Overview

Sprint 8 builds the TeamMemoryOS web frontend from scratch using React 18, TypeScript, Vite, Tailwind CSS, Shadcn UI, React Query, Zustand, React Router v6, React Hook Form, React Flow, and Framer Motion. The frontend surfaces all backend capabilities built in Sprints 1–7 — organizational memory, hybrid GraphRAG retrieval, the knowledge graph, the AI engineering copilot, and the multi-agent platform — as a premium desktop-first AI Operating System interface.

The frontend folder already exists at `frontend/` with empty subdirectories. No React app scaffolding exists yet. Every milestone in this sprint builds on top of prior milestones in strict dependency order.

This document is the **official implementation blueprint**. Every milestone section includes: Goal, Features, Backend APIs, React Components, Folder Additions, State Management, Accessibility, Security, Testing, Performance, and Validation Checklist.

---

## Milestone Order

```
8.0 Frontend Foundation      ← Blocks everything. Build once, reuse everywhere.
  ↓
8.1 Authentication & Dashboard   ← Auth shell + live dashboard widgets.
  ↓
8.2 Memory Workspace         ← Memory CRUD, search, scenarios.
  ↓ (parallel opportunity)
8.3 Knowledge Graph          ← Entity/relationship graph. Parallel with 8.2.
  ↓
8.4 AI Chat & Explainability ← RAG chat, citations, graph path, confidence.
  ↓
8.5 Multi-Agent Workspace    ← Agent registry, workflow runner, debug/repo panels.
  ↓
8.6 Final Integration & QA   ← E2E validation, accessibility audit, performance pass.
```

---

## Folder Structure

The following folder structure is the canonical enterprise-grade layout for this project. Every developer must respect folder responsibilities.

```
frontend/
  app/                ← React Router route tree only. No business logic here.
    index.tsx         ← Router root, QueryClientProvider, global providers
    routes.tsx        ← Centralized route definitions with lazy() wrappers
  layouts/            ← Full-page layout wrappers (AppShell, AuthLayout)
    AppShell.tsx
    AuthLayout.tsx
  components/         ← Reusable design system primitives. NO feature logic.
    ui/               ← Shadcn-based design system components
    auth/             ← AuthGuard, ProtectedRoute
    feedback/         ← LoadingState, EmptyState, ErrorState, Skeleton, Spinner
    graph/            ← Shared React Flow node/edge primitives
  features/           ← Feature modules. Each feature is self-contained.
    auth/             ← LoginPage, useLogin hook
    dashboard/        ← DashboardPage, widgets
    memory/           ← MemoryPage, MemoryTable, CreateMemoryDialog
    scenarios/        ← ScenarioList, CreateScenarioDialog
    graph/            ← KnowledgeGraphPage, GraphCanvas, EntityDetailPanel
    chat/             ← ChatPage, ChatMessageList, CitationPanel, ConfidenceBadge
    retrieval/        ← RetrievalExplainPage, RetrievalResultCard
    engineering/      ← EngineeringCopilotPage, DebugPanel, PRReviewPanel
    agents/           ← AgentsPage, AgentCard, WorkflowRunPanel, DebugAgentPanel
  services/           ← All API calls. One function per endpoint. Typed I/O.
    authService.ts
    healthService.ts
    memoryService.ts
    scenarioService.ts
    entityService.ts
    relationshipService.ts
    chatService.ts
    retrievalService.ts
    engineeringService.ts
    agentsService.ts
    gitService.ts
    usersService.ts
  hooks/              ← Reusable custom hooks (not feature-specific).
    useAuth.ts
    usePagination.ts
    useDebounce.ts
    useOrganization.ts
  stores/             ← Zustand stores. Client UI state only. No server data.
    authStore.ts
    uiStore.ts
    workspaceStore.ts
    graphStore.ts
    chatStore.ts
    agentStore.ts
  lib/                ← Low-level utilities and configuration.
    api.ts            ← Single Axios instance with interceptors
    queryClient.ts    ← React Query client configuration
    cn.ts             ← Tailwind class merge utility
  utils/              ← Pure functions. No React. No side effects.
    formatDate.ts
    truncate.ts
    colorFromType.ts
    scoreToLabel.ts
  styles/             ← Global CSS and design tokens.
    globals.css
    tokens.css
  types/              ← Shared TypeScript interfaces. Mirror backend schemas.
    api.ts            ← Base types: ApiError, PaginatedResponse
    auth.ts
    memory.ts
    scenario.ts
    entity.ts
    relationship.ts
    chat.ts
    retrieval.ts
    engineering.ts
    agents.ts
  assets/             ← Static assets: logos, icons, images.
  index.html
  main.tsx
  vite.config.ts
  tailwind.config.ts
  tsconfig.json
  package.json
  .env.example
```

### Folder Responsibility Rules

| Folder | Owns | Never contains |
|---|---|---|
| `app/` | Route definitions, providers | Business logic, API calls |
| `layouts/` | Full-page structural wrappers | Feature logic |
| `components/` | Design system primitives | API calls, business state |
| `features/` | Feature pages + feature-local components | Direct `fetch()` or `axios` calls |
| `services/` | One function per API endpoint | React components, hooks |
| `hooks/` | Reusable hook logic | Component JSX |
| `stores/` | Client-only UI state | Server response data |
| `lib/` | Config instances (axios, queryClient) | Feature logic |
| `utils/` | Pure helper functions | React, side effects |
| `types/` | TypeScript interface definitions | Runtime logic |

---

## Design System Architecture

The design system is defined once in `components/ui/` and `styles/`. Every feature reuses these primitives. No feature may define its own color palette, spacing scale, or primitive components.

### Color Palette

```css
/* styles/tokens.css */
:root {
  /* Background layers */
  --color-bg-base:        #0a0a0f;   /* Deepest canvas */
  --color-bg-surface:     #111118;   /* Cards, panels */
  --color-bg-elevated:    #1a1a24;   /* Dropdowns, dialogs */
  --color-bg-subtle:      #22222f;   /* Hover states, row highlights */

  /* Brand */
  --color-brand-primary:  #6366f1;   /* Indigo — primary actions */
  --color-brand-hover:    #818cf8;   /* Indigo light — hover */
  --color-brand-muted:    #312e81;   /* Indigo dark — muted bg */

  /* Semantic */
  --color-success:        #22c55e;
  --color-warning:        #f59e0b;
  --color-danger:         #ef4444;
  --color-info:           #38bdf8;

  /* Text */
  --color-text-primary:   #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-text-muted:     #475569;
  --color-text-inverse:   #0a0a0f;

  /* Borders */
  --color-border:         #1e1e2e;
  --color-border-subtle:  #16161f;
  --color-border-focus:   #6366f1;

  /* Confidence banding */
  --color-conf-high:      #22c55e;   /* > 0.75 */
  --color-conf-med:       #f59e0b;   /* 0.5 – 0.75 */
  --color-conf-low:       #ef4444;   /* < 0.5 */
}
```

### Typography

```css
/* Font stack */
--font-sans:  'Inter', system-ui, sans-serif;
--font-mono:  'JetBrains Mono', 'Fira Code', monospace;

/* Scale */
--text-xs:    0.75rem;    /* Labels, badges */
--text-sm:    0.875rem;   /* Body secondary */
--text-base:  1rem;       /* Body primary */
--text-lg:    1.125rem;   /* Subheadings */
--text-xl:    1.25rem;    /* Section headings */
--text-2xl:   1.5rem;     /* Page headings */
--text-3xl:   1.875rem;   /* Hero headings */

/* Weight */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing Scale

4px base unit. All spacing uses multiples of 4.

```
1 = 4px | 2 = 8px | 3 = 12px | 4 = 16px | 5 = 20px | 6 = 24px
8 = 32px | 10 = 40px | 12 = 48px | 16 = 64px | 20 = 80px | 24 = 96px
```

### Radius Scale

```css
--radius-sm:   4px;
--radius-md:   8px;
--radius-lg:   12px;
--radius-xl:   16px;
--radius-full: 9999px;  /* Pills, badges */
```

### Elevation / Shadow System

```css
--shadow-sm:   0 1px 2px rgba(0,0,0,0.4);
--shadow-md:   0 4px 12px rgba(0,0,0,0.5);
--shadow-lg:   0 8px 24px rgba(0,0,0,0.6);
--shadow-glow: 0 0 20px rgba(99,102,241,0.2);  /* Brand glow for active states */
```

### Icon System

Use **Lucide React** exclusively. Never import SVGs directly into feature components. Icon sizes are standardized: `16px` (inline), `20px` (button), `24px` (navigation).

### Animation Rules

Use **Framer Motion** for page transitions and panel entrances. Use CSS `transition` for hover/focus micro-interactions only.

- Page entrance: `opacity 0→1`, `y +8px→0`, duration `200ms`, ease `easeOut`.
- Panel slide-in: `x +16px→0`, duration `180ms`.
- Skeleton pulse: CSS `animate-pulse`.
- No animations on data tables — only skeleton loading.
- Respect `prefers-reduced-motion`: all Framer Motion animations must check `useReducedMotion()`.

### Component Library

All components live in `components/ui/`. They wrap Shadcn primitives with project-specific tokens applied.

| Component | Purpose |
|---|---|
| `Button` | Primary, secondary, ghost, destructive variants |
| `Input` | Text input with label, error, and hint slots |
| `Card` | Surface container with optional header/footer |
| `Badge` | Semantic type label (success, warning, danger, info, default) |
| `Dialog` | Modal with focus trap, ESC close, accessible title |
| `Drawer` | Slide-in side panel for detail views |
| `Table` | Sortable, accessible data table with column headers |
| `Tabs` | Horizontal tab group with keyboard navigation |
| `Tooltip` | Hover/focus disclosure for icon-only controls |
| `Dropdown` | Accessible dropdown menu with keyboard support |
| `Skeleton` | Loading placeholder matching component shape |
| `Spinner` | Inline loading indicator with `aria-label` |
| `EmptyState` | Zero-data state with icon, heading, CTA |
| `ErrorState` | Error boundary fallback with retry action |
| `LoadingState` | Full-panel loading with skeleton grid |

**Reuse Rule:** Before creating any new UI element, check `components/ui/` first. Never redefine a color, shadow, or spacing value inline — use CSS variables. Components must stay under 200 lines.

---

## API Architecture

### Single Axios Client (`lib/api.ts`)

One Axios instance is created at startup. All service functions import from this file. No component ever calls `fetch()` or creates its own Axios instance.

**Request interceptor responsibilities:**
1. Attach `Authorization: Bearer <token>` from `authStore`.
2. Inject `X-Organization-ID` header from `authStore.organization_id`.
3. Attach request timestamp for debugging.

**Response interceptor responsibilities:**
1. On `401` → clear `authStore`, redirect to `/login`.
2. Normalize all errors into a typed `ApiError` object: `{ message, status, code }`.
3. Never let raw Axios errors propagate into feature components.

**Request cancellation:**
- Use `AbortController` signals passed via React Query's `signal` parameter.
- All list/search queries must be cancellable.
- Do not cancel mutations.

**Typed responses:**
- Every service function has an explicit return type annotation.
- Response shapes mirror backend Pydantic schema field names exactly.
- Shared interfaces live in `types/`.

### Organization Context

After login, `org_id` is stored in `authStore`. The Axios request interceptor reads it automatically. No feature component needs to pass `org_id` as a prop.

---

## React Query Architecture

React Query owns **all server state**. It is the single source of truth for any data that comes from the API.

### Cache Key Convention

```
['resource', scopeId, ...filters]

Examples:
['memory', orgId]
['memory', orgId, scenarioId]
['memory', 'detail', entryId]
['entities', orgId]
['entities', 'detail', entityId]
['agents']
['agents', 'detail', agentName]
['health']
```

### staleTime Strategy

| Data type | staleTime | Reason |
|---|---|---|
| Health check | 30 seconds | Needs to reflect backend status |
| Memory entries | 60 seconds | Changes infrequently per session |
| Scenarios | 2 minutes | Low-churn metadata |
| Entities / Relationships | 2 minutes | Graph rarely changes mid-session |
| Agent registry | 5 minutes | Static capability metadata |
| Chat responses | `Infinity` | User-triggered mutations; never re-fetched |

### gcTime Strategy

Default `gcTime` of 5 minutes. Extend to 10 minutes for entity/relationship data to support graph navigation without refetches.

### Mutation Invalidation Rules

After a successful mutation, invalidate the relevant list query:
- Create memory entry → invalidate `['memory', orgId]`
- Create scenario → invalidate `['scenarios', orgId]`
- Workflow run → invalidate nothing (append to `chatStore`)

### Optimistic Updates

Apply optimistic updates **only** for status toggles and simple field updates. Never apply optimistic updates for creates (unknown server-generated IDs). Roll back on error and show a toast notification.

### Prefetch After Login

After successful login, prefetch:
1. `GET /api/v1/health`
2. `GET /api/v1/scenarios/organization/{org_id}`
3. `GET /api/v1/agents/`

This ensures the Dashboard renders instantly without skeleton loading for the most critical widgets.

### Retry Policy

```typescript
retry: (failureCount, error) => {
  if (error.status === 401 || error.status === 403 || error.status === 404) return false;
  return failureCount < 2;
}
```

### Pagination

Use cursor-based or offset pagination depending on backend support. Default page size: 20. All list queries accept `{ page, limit }` parameters. Use `keepPreviousData: true` to prevent table flash on page change.

### Infinite Scrolling

Use `useInfiniteQuery` for chat message history and memory search results where the user scrolls to load more.

---

## Zustand Architecture

Zustand manages **client-side UI state only**. Never store server response data in Zustand.

### What belongs in Zustand

- Auth token, user object, org_id (persisted to localStorage)
- Theme preference, sidebar collapsed state
- Currently selected IDs (not the data itself)
- Chat conversation history (user messages + AI responses assembled client-side)
- Graph selection state (selected entity ID, expanded nodes)
- Agent panel active tab, last workflow result

### What never belongs in Zustand

- API response lists (memory entries, entities, agents) — that is React Query's job
- Loading/error states for server requests — React Query owns those
- Form values — React Hook Form owns those

### Store Definitions

| Store | State | Purpose |
|---|---|---|
| `authStore` | token, user, org_id | JWT session, persisted |
| `uiStore` | sidebarCollapsed, theme, toasts | UI preferences |
| `workspaceStore` | activeSection, breadcrumbs | Navigation state |
| `graphStore` | selectedEntityId, expandedNodeIds, filterType, layoutMode | Graph interaction |
| `chatStore` | messages[], activeMode, isLoading, lastMetadata | Chat session |
| `agentStore` | activePanel, selectedAgentName, workflowHistory[] | Agent workspace |

---

## Milestone 8.0 — Frontend Foundation

### Why This Milestone Exists

All subsequent milestones depend on a correctly configured build system, design token system, component library, and global provider tree. Building these once — and correctly — avoids rework in every downstream milestone. A missing CSS variable, an incorrectly configured Tailwind prefix, or a missing provider at the app root would cause cascading failures across all features. This milestone is infrastructure, not a feature.

### Goal

Bootstrap the Vite + React + TypeScript project, configure Tailwind CSS and Shadcn UI with the full TeamMemoryOS design token system, establish the global provider tree, and build every shared UI primitive that downstream milestones will consume.

### Features

- Vite + React 18 + TypeScript scaffold
- Tailwind CSS with custom design tokens
- Shadcn UI initialization with component overrides
- CSS variable design token system (`styles/tokens.css`)
- Typography, color, spacing, radius, shadow, animation tokens
- Inter + JetBrains Mono font setup
- Lucide React icon integration
- ThemeProvider (dark mode by default)
- Global providers tree: QueryClientProvider, RouterProvider, ThemeProvider
- All UI primitive components (full list in Design System section)
- Global Framer Motion animation variants
- Global `LoadingState`, `EmptyState`, `ErrorState`, `Skeleton`, `Spinner`
- `lib/api.ts` — Axios client with interceptors (no auth logic yet, just structure)
- `lib/queryClient.ts` — React Query client with retry/staleTime defaults
- `lib/cn.ts` — Tailwind class merge utility
- `utils/` — date, truncate, color, score helpers
- TypeScript path aliases (`@/` → `src/`)
- `.env.example` with `VITE_API_BASE_URL`
- Vitest + React Testing Library + MSW test infrastructure setup
- `package.json` with all dependencies pinned

### Backend APIs Required

None. This milestone has no backend integration. It is purely frontend infrastructure.

### React Components

| Component | Location | Notes |
|---|---|---|
| `Button` | `components/ui/Button.tsx` | 4 variants, loading state, icon slot |
| `Input` | `components/ui/Input.tsx` | Label, error, hint slots |
| `Card` | `components/ui/Card.tsx` | Header, body, footer slots |
| `Badge` | `components/ui/Badge.tsx` | 6 semantic variants |
| `Dialog` | `components/ui/Dialog.tsx` | Focus trap, ESC, accessible title |
| `Drawer` | `components/ui/Drawer.tsx` | Side panel with overlay |
| `Table` | `components/ui/Table.tsx` | th scope, keyboard rows |
| `Tabs` | `components/ui/Tabs.tsx` | Keyboard navigation |
| `Tooltip` | `components/ui/Tooltip.tsx` | Hover + focus disclosure |
| `Dropdown` | `components/ui/Dropdown.tsx` | Keyboard operable |
| `Skeleton` | `components/ui/Skeleton.tsx` | Shape-matched loading |
| `Spinner` | `components/ui/Spinner.tsx` | aria-label required |
| `EmptyState` | `components/feedback/EmptyState.tsx` | Icon, heading, CTA |
| `ErrorState` | `components/feedback/ErrorState.tsx` | Retry action |
| `LoadingState` | `components/feedback/LoadingState.tsx` | Full-panel skeleton grid |

### Folder Additions

```
frontend/
  app/index.tsx
  app/routes.tsx
  components/ui/          ← All 12 primitives
  components/feedback/    ← EmptyState, ErrorState, LoadingState
  lib/api.ts
  lib/queryClient.ts
  lib/cn.ts
  utils/
  styles/globals.css
  styles/tokens.css
  types/api.ts
  index.html
  main.tsx
  vite.config.ts
  tailwind.config.ts
  tsconfig.json
  package.json
  .env.example
```

### State Management

None in this milestone. `lib/api.ts` is scaffolded but auth interceptor is wired in Milestone 8.1 once `authStore` exists.

### Accessibility

- All UI primitives ship with correct ARIA roles and attributes.
- `Dialog` has `role="dialog"`, `aria-modal="true"`, `aria-labelledby`.
- `Button` has `aria-disabled` instead of the `disabled` attribute when showing loading state.
- All color tokens meet WCAG AA contrast ratio (4.5:1 minimum for text, 3:1 for UI elements).
- Tailwind configuration includes `aria-*` variant support.

### Security

- No secrets or environment values are embedded in the build output.
- `VITE_API_BASE_URL` is the only runtime config value.
- Strict TypeScript (`"strict": true` in `tsconfig.json`).
- No `dangerouslySetInnerHTML` in any primitive component.

### Testing Checklist

- [ ] Vitest + React Testing Library + MSW installed and running
- [ ] Snapshot test for each UI primitive (Button, Card, Badge, Spinner, EmptyState)
- [ ] All components render without console errors
- [ ] Tailwind tokens resolve correctly in test environment

### Performance

- All route components are wrapped in `React.lazy()` from Milestone 8.1 onward.
- Shadcn components are imported individually — no full-library barrel imports.
- Lucide icons are imported individually — no barrel imports.

### Validation Checklist

- [ ] `npm run dev` starts without errors
- [ ] `npm run build` produces clean output with no TypeScript errors
- [ ] `npm test` runs and passes all primitive component tests
- [ ] Design tokens render correctly in browser (inspect CSS variables in DevTools)
- [ ] EmptyState, LoadingState, ErrorState all render in Storybook or test harness
- [ ] Tailwind purge is configured for `frontend/src/**`
- [ ] Path alias `@/` resolves correctly

---

## Milestone 8.1 — Authentication & Dashboard

### Goal

Implement the complete authentication flow (login, logout, JWT storage, route guarding, unauthorized redirect), build the AppShell layout (Sidebar + Topbar), and create the Dashboard page with live backend health and organization summary widgets.

### Features

- Login page with form validation
- JWT storage in `authStore` (Zustand, persisted to localStorage)
- `AuthGuard` — redirects unauthenticated users to `/login`
- `ProtectedRoute` — wraps all authenticated routes
- Logout action with store clear and redirect
- Session restore on page refresh (read token from localStorage)
- Token refresh placeholder (hook exists, backend endpoint not yet implemented)
- `AppShell` — persistent layout wrapping Sidebar + Topbar + main content area
- Sidebar navigation with active route highlight
- Topbar with organization name, user display, logout button
- Dashboard with 6 live widgets (see widget table below)
- Prefetch scenarios and agents after login

### Dashboard Widgets

| Widget | Backend API | Description |
|---|---|---|
| Backend Health | `GET /api/v1/health/` | Green/red indicator + latency |
| Database Health | `GET /api/v1/health/db` | PostgreSQL connection status |
| Memory Statistics | `GET /api/v1/memory/organization/{org_id}` | Total entries count by type |
| Scenario Overview | `GET /api/v1/scenarios/organization/{org_id}` | Scenario count + names |
| Agent Registry | `GET /api/v1/agents/` | Count of registered agents |
| Quick Actions | Static | Shortcut buttons to Memory, Chat, Graph, Agents |

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/login` | OAuth2 password form → JWT |
| `GET /api/v1/health/` | App health widget |
| `GET /api/v1/health/db` | DB health widget |
| `GET /api/v1/memory/organization/{org_id}` | Memory stats widget |
| `GET /api/v1/scenarios/organization/{org_id}` | Scenario overview widget |
| `GET /api/v1/agents/` | Agent registry widget |

### React Components

| Component | Location |
|---|---|
| `LoginPage` | `features/auth/LoginPage.tsx` |
| `AuthGuard` | `components/auth/AuthGuard.tsx` |
| `ProtectedRoute` | `components/auth/ProtectedRoute.tsx` |
| `AppShell` | `layouts/AppShell.tsx` |
| `AuthLayout` | `layouts/AuthLayout.tsx` |
| `Sidebar` | `layouts/Sidebar.tsx` |
| `Topbar` | `layouts/Topbar.tsx` |
| `DashboardPage` | `features/dashboard/DashboardPage.tsx` |
| `HealthWidget` | `features/dashboard/HealthWidget.tsx` |
| `MemoryStatsWidget` | `features/dashboard/MemoryStatsWidget.tsx` |
| `ScenarioOverviewWidget` | `features/dashboard/ScenarioOverviewWidget.tsx` |
| `AgentRegistryWidget` | `features/dashboard/AgentRegistryWidget.tsx` |
| `QuickActionsWidget` | `features/dashboard/QuickActionsWidget.tsx` |

### Folder Additions

```
features/
  auth/
    LoginPage.tsx
    useLogin.ts
  dashboard/
    DashboardPage.tsx
    HealthWidget.tsx
    MemoryStatsWidget.tsx
    ScenarioOverviewWidget.tsx
    AgentRegistryWidget.tsx
    QuickActionsWidget.tsx
layouts/
  AppShell.tsx
  AuthLayout.tsx
  Sidebar.tsx
  Topbar.tsx
components/
  auth/
    AuthGuard.tsx
    ProtectedRoute.tsx
services/
  authService.ts
  healthService.ts
stores/
  authStore.ts
  uiStore.ts
hooks/
  useAuth.ts
  useOrganization.ts
types/
  auth.ts
```

### State Management

- **Zustand** — `authStore`: `access_token`, `user`, `organization_id`. Persist to localStorage via `persist` middleware.
- **Zustand** — `uiStore`: `sidebarCollapsed`, `theme`.
- **React Query** — health check query (`staleTime: 30s`), memory stats, scenario count, agent registry (prefetched after login).
- **React Hook Form** — Login form with `email` + `password` fields.

### Routing

| Route | Component | Protected |
|---|---|---|
| `/login` | `LoginPage` inside `AuthLayout` | No |
| `/` | `DashboardPage` inside `AppShell` | Yes |
| `/*` | Child routes inside `AppShell` | Yes |

### Accessibility

- Login form: `<label>` for each input, `aria-required`, `aria-describedby` for errors.
- Login button: `aria-busy="true"` during submission, `aria-disabled` when form is invalid.
- Sidebar: `<nav role="navigation" aria-label="Main navigation">`.
- Active sidebar item: `aria-current="page"`.
- Keyboard navigation through sidebar items with `Tab` and `Enter`.
- Dashboard widgets: `role="region"` with `aria-labelledby` pointing to widget heading.

### Security

- JWT stored in `localStorage` (accepted trade-off for SPA; document in security section).
- Token never logged to console.
- Logout clears entire `authStore` state and removes localStorage entry.
- `AuthGuard` renders nothing (not a loading state) until auth state is resolved, preventing flash of authenticated content.
- Login error messages are generic — do not reveal whether email or password was incorrect.

### Testing Checklist

- [ ] `useLogin` hook: test successful login stores token and redirects
- [ ] `useLogin` hook: test failed login sets error state
- [ ] `AuthGuard`: renders children when authenticated, redirects when not
- [ ] `LoginPage`: form validation errors display correctly
- [ ] `authStore`: persists and restores from localStorage
- [ ] `DashboardPage`: renders all 6 widgets with MSW-mocked responses
- [ ] `HealthWidget`: shows green when healthy, red when unhealthy

### Performance

- Dashboard widgets load in parallel (independent React Query queries).
- Sidebar route components use `React.lazy()` — not loaded until navigation.
- Login page is the only eagerly loaded route.

### Validation Checklist

- [ ] Login with valid credentials stores JWT and redirects to `/`
- [ ] Invalid credentials shows error message without revealing which field failed
- [ ] Unauthenticated `GET /` redirects to `/login`
- [ ] Logout clears state and redirects to `/login`
- [ ] Page refresh restores authenticated session
- [ ] All 6 dashboard widgets render live data
- [ ] Sidebar highlights active route
- [ ] Sidebar collapse works on desktop

---

## Milestone 8.2 — Memory Workspace

### Goal

Build the organizational memory interface: paginated list of memory entries by scenario, semantic search, create/view entries, scenario management, and memory link display.

### Features

- Memory entry list table with pagination (20 per page)
- Filter by scenario (sidebar navigation)
- Semantic search with 300ms debounce
- Memory entry detail drawer (not a new page)
- Create memory entry dialog with form validation
- Scenario list sidebar
- Create scenario dialog
- Memory type badges (DECISION, CODE, DISCUSSION, DOCUMENTATION, INCIDENT)
- Memory link display on entry detail
- Bulk action scaffolding (future-ready: checkboxes in table, disabled action bar)
- Empty state when no memories exist
- Error state for failed API requests

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/memory/organization/{org_id}` | List entries (paginated) |
| `POST /api/v1/memory/` | Create entry |
| `GET /api/v1/memory/{entry_id}` | Entry detail |
| `POST /api/v1/memory/search` | Semantic search |
| `GET /api/v1/scenarios/organization/{org_id}` | List scenarios |
| `POST /api/v1/scenarios/` | Create scenario |
| `GET /api/v1/scenarios/{id}` | Scenario detail |
| `GET /api/v1/memory-links` | Memory link list |

### React Components

| Component | Location |
|---|---|
| `MemoryPage` | `features/memory/MemoryPage.tsx` |
| `MemoryTable` | `features/memory/MemoryTable.tsx` |
| `MemoryEntryDrawer` | `features/memory/MemoryEntryDrawer.tsx` |
| `CreateMemoryDialog` | `features/memory/CreateMemoryDialog.tsx` |
| `MemorySearchBar` | `features/memory/MemorySearchBar.tsx` |
| `MemoryTypeBadge` | `features/memory/MemoryTypeBadge.tsx` |
| `ScenarioSidebar` | `features/scenarios/ScenarioSidebar.tsx` |
| `ScenarioList` | `features/scenarios/ScenarioList.tsx` |
| `CreateScenarioDialog` | `features/scenarios/CreateScenarioDialog.tsx` |

### Folder Additions

```
features/
  memory/
  scenarios/
services/
  memoryService.ts
  scenarioService.ts
types/
  memory.ts
  scenario.ts
```

### State Management

- **React Query** — `['memory', orgId]`, `['memory', orgId, scenarioId]`, `['memory', 'detail', entryId]`, `['scenarios', orgId]`.
- **React Query** — `useMutation` for create memory, create scenario. Invalidate list on success.
- **Zustand** — `workspaceStore.activeScenarioId` for scenario navigation selection.
- **React Hook Form** — `CreateMemoryDialog`, `CreateScenarioDialog` validation.

### Routing

| Route | Component |
|---|---|
| `/memory` | `MemoryPage` (list + search) |
| `/scenarios` | `ScenarioList` (renders in `MemoryPage` sidebar) |

Memory entry detail opens in a `Drawer` component — no separate route. This keeps the URL stable while showing detail.

### Accessibility

- Table: `<th scope="col">` on all column headers. Row click opens drawer, not navigation.
- Search: `role="search"`, `aria-label="Search memory entries"`, debounced.
- Create dialog: focus moves to dialog heading on open, returns to trigger button on close. `ESC` closes.
- Memory type badges: text label + icon, not color-only indicators.
- Scenario sidebar: `role="list"`, each item `role="listitem"`.
- Drawer: `role="complementary"`, `aria-label="Memory entry detail"`.

### Security

- `org_id` injected via Axios interceptor — never accepted from URL params.
- Memory entry content is rendered as plain text — no HTML rendering of user content.

### Testing Checklist

- [ ] `MemoryTable`: renders list with MSW mock; shows skeleton while loading
- [ ] `MemorySearchBar`: debounce fires search after 300ms, not on every keystroke
- [ ] `CreateMemoryDialog`: validates required fields; submits and invalidates cache
- [ ] `useMemory` hook: handles pagination correctly
- [ ] `ScenarioList`: renders scenario names; selecting one filters the table
- [ ] Empty state renders when `GET /memory` returns empty array
- [ ] Error state renders when `GET /memory` fails with 500

### Performance

- Memory table uses `keepPreviousData: true` during pagination.
- `MemorySearchBar` debounces 300ms before firing query.
- `Drawer` is lazy-rendered — DOM not inserted until first open.
- Memory entry content truncated at 200 characters in table view.

### Validation Checklist

- [ ] Memory list loads and paginates correctly
- [ ] Create memory entry form validates required fields and submits
- [ ] Semantic search returns results or empty state
- [ ] Scenario list loads; selecting a scenario filters the memory table
- [ ] Entry detail drawer shows all fields including type, timestamps, content
- [ ] Loading skeletons appear during API calls
- [ ] Error states shown for failed requests
- [ ] Responsive on tablet viewport
- [ ] Bulk action checkboxes visible in table (disabled, future-ready)

---

## Milestone 8.3 — Knowledge Graph Viewer

### Goal

Build an interactive knowledge graph visualization using React Flow. Display entities as nodes, relationships as directed edges, support entity type filtering, neighbor expansion, entity and relationship inspector panels, mini-map, zoom controls, and a full accessibility fallback table.

### Features

- React Flow canvas with entity nodes and relationship edges
- Node color by entity type
- Click node → entity inspector panel (Drawer)
- Click edge → relationship inspector (tooltip or inline panel)
- Expand neighbors on demand (lazy-load edges per node)
- Entity type filter chips
- Full-text entity search with debounce
- Mini-map for large graphs
- Zoom in / zoom out / fit-to-view controls
- List/Table fallback for screen reader users
- Empty state when no entities exist
- Entity links back to related memory entries

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/entities/organization/{org_id}` | Load all entities |
| `GET /api/v1/entities/{entity_id}` | Entity detail |
| `GET /api/v1/relationships/entity/{id}/outgoing` | Directed edges |
| `GET /api/v1/relationships/entity/{id}/neighbors` | Neighbor expansion |
| `GET /api/v1/relationships/{relationship_id}` | Relationship detail |
| `GET /api/v1/entities/memory/{memory_id}` | Entities for a memory entry |

### React Components

| Component | Location |
|---|---|
| `KnowledgeGraphPage` | `features/graph/KnowledgeGraphPage.tsx` |
| `GraphCanvas` | `features/graph/GraphCanvas.tsx` |
| `EntityNode` | `features/graph/nodes/EntityNode.tsx` |
| `RelationshipEdge` | `features/graph/edges/RelationshipEdge.tsx` |
| `EntityInspectorPanel` | `features/graph/EntityInspectorPanel.tsx` |
| `RelationshipInspector` | `features/graph/RelationshipInspector.tsx` |
| `GraphFilterBar` | `features/graph/GraphFilterBar.tsx` |
| `GraphSearchInput` | `features/graph/GraphSearchInput.tsx` |
| `EntityFallbackTable` | `features/graph/EntityFallbackTable.tsx` |
| `GraphControls` | `features/graph/GraphControls.tsx` |

### Folder Additions

```
features/
  graph/
    nodes/
    edges/
services/
  entityService.ts
  relationshipService.ts
types/
  entity.ts
  relationship.ts
```

### State Management

- **React Query** — `['entities', orgId]` with `staleTime: 2min`. Per-entity neighbor queries `['neighbors', entityId]`.
- **Zustand** — `graphStore`: `selectedEntityId`, `expandedNodeIds[]`, `filterType`, `searchTerm`, `layoutMode`.
- React Flow manages internal canvas state via `useNodesState` and `useEdgesState`.

### Routing

| Route | Component |
|---|---|
| `/graph` | `KnowledgeGraphPage` |

### Accessibility

- `GraphCanvas`: `role="application"`, `aria-label="Knowledge graph visualization"`.
- Every entity node: focusable via `Tab`, `Enter` to open inspector, `Space` to expand neighbors.
- `EntityFallbackTable`: always rendered below the canvas (`sr-only` class by default), visible when user enables "Accessible View" toggle.
- Filter chips: `role="group"`, `aria-label="Filter by entity type"`, each chip is a toggle button with `aria-pressed`.
- Inspector panel: `role="complementary"`, `aria-label="Entity details"`.
- Relationship inspector: accessible as tooltip with `role="tooltip"`.

### Security

- Entity name and description rendered as plain text — no HTML rendering.
- Graph data scoped to `org_id` — enforced by backend, validated by service layer type checking.

### Testing Checklist

- [ ] `GraphCanvas`: renders nodes and edges with MSW-mocked entity/relationship data
- [ ] `EntityNode`: focus and keyboard activation tested
- [ ] `GraphFilterBar`: filter chips correctly filter visible nodes
- [ ] `EntityFallbackTable`: renders all entities in accessible table format
- [ ] Neighbor expansion triggers correct API call and adds nodes to canvas
- [ ] Empty state renders when entity list is empty

### Performance

- React Flow `nodesDraggable: false` by default (enable only in debug mode) — reduces re-renders.
- Neighbor expansion is lazy: only load edges for a node when it is clicked.
- Entity list capped at 500 nodes before showing a "load more" pagination control — React Flow degrades above this.
- `GraphCanvas` wrapped in `React.memo()`.
- Use `useCallback` for all node/edge event handlers.

### Validation Checklist

- [ ] Graph renders all entities as nodes with correct type coloring
- [ ] Edges render with relationship type labels
- [ ] Clicking a node opens the inspector panel
- [ ] Neighbor expansion loads and adds new nodes/edges
- [ ] Entity type filter shows/hides node categories correctly
- [ ] Graph search filters visible nodes in real time
- [ ] Empty state when no entities exist
- [ ] Accessible fallback table is available
- [ ] Mini-map and zoom controls function

---

## Milestone 8.4 — AI Chat & Explainability Workspace

### Goal

Build the primary AI interaction surface: a stateful chat interface backed by the hybrid RAG pipeline, a full explainability panel (citations, graph path, confidence, retrieval mode, participating agents), a retrieval explain view for debugging, and the Engineering Copilot panel (chat, debug, PR review modes).

### Granite Integration Points

- `POST /api/v1/chat/ask` → IBM Granite powers the RAG generation. The response includes `answer`, `citations`, `confidence`, `graph_path`, `retrieval_mode`, `participating_agents`, `suggested_actions`.
- `POST /api/v1/engineering/chat` → Engineering Copilot powered by Granite with code-aware prompt engineering.
- `POST /api/v1/engineering/debug` → Stack trace analysis via Granite.
- `POST /api/v1/engineering/review` → PR review analysis via Granite.
- `POST /api/v1/retrieval/explain` → Retrieval explanation without LLM (deterministic scoring only).

Every Granite response surface must show all explainability fields. These fields are **never hidden**.

### Features

- Stateful chat conversation (messages persisted in `chatStore` for session lifetime)
- Conversation sidebar (chat history list)
- Chat input with `Enter` to send, `Shift+Enter` for newline, character count
- Mode selector: General RAG / Hybrid GraphRAG / Engineering Copilot
- Streaming-ready architecture (messages built to accept streaming text; streaming not enabled until backend supports SSE)
- Citations panel: memory title, type, vector score, graph score, rank
- Confidence badge: numeric value + color band (green/amber/red)
- Retrieval mode tag: semantic / hybrid / engineering
- Graph path: entity traversal chain rendered as breadcrumb
- Participating agents: badge list per response
- Suggested actions: rendered as clickable button row
- Markdown rendering with safe sanitization
- Code block rendering with syntax highlight and copy button
- Retrieval Explain page: direct retrieval with per-result score breakdown
- Engineering Copilot panel: chat, debug, and PR review sub-modes

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/chat/ask` | RAG chat |
| `POST /api/v1/retrieval/hybrid-search` | Direct retrieval |
| `POST /api/v1/retrieval/explain` | Retrieval explanation |
| `POST /api/v1/engineering/chat` | Engineering copilot |
| `POST /api/v1/engineering/debug` | Debug analysis |
| `POST /api/v1/engineering/review` | PR review |

### React Components

| Component | Location |
|---|---|
| `ChatPage` | `features/chat/ChatPage.tsx` |
| `ConversationSidebar` | `features/chat/ConversationSidebar.tsx` |
| `ChatMessageList` | `features/chat/ChatMessageList.tsx` |
| `ChatMessage` | `features/chat/ChatMessage.tsx` |
| `ChatInput` | `features/chat/ChatInput.tsx` |
| `ChatModeSelector` | `features/chat/ChatModeSelector.tsx` |
| `CitationPanel` | `features/chat/CitationPanel.tsx` |
| `CitationCard` | `features/chat/CitationCard.tsx` |
| `ConfidenceBadge` | `features/chat/ConfidenceBadge.tsx` |
| `RetrievalModeTag` | `features/chat/RetrievalModeTag.tsx` |
| `GraphPathBreadcrumb` | `features/chat/GraphPathBreadcrumb.tsx` |
| `ParticipatingAgentsList` | `features/chat/ParticipatingAgentsList.tsx` |
| `SuggestedActionsBar` | `features/chat/SuggestedActionsBar.tsx` |
| `MarkdownRenderer` | `features/chat/MarkdownRenderer.tsx` |
| `CodeBlock` | `features/chat/CodeBlock.tsx` |
| `RetrievalExplainPage` | `features/retrieval/RetrievalExplainPage.tsx` |
| `RetrievalResultCard` | `features/retrieval/RetrievalResultCard.tsx` |
| `ScoreBreakdown` | `features/retrieval/ScoreBreakdown.tsx` |
| `EngineeringCopilotPage` | `features/engineering/EngineeringCopilotPage.tsx` |
| `DebugPanel` | `features/engineering/DebugPanel.tsx` |
| `PRReviewPanel` | `features/engineering/PRReviewPanel.tsx` |

### Shared Components (Produced Here, Reused in 8.5)

`CitationPanel`, `ConfidenceBadge`, `RetrievalModeTag`, `GraphPathBreadcrumb`, `ParticipatingAgentsList`, `SuggestedActionsBar`, `MarkdownRenderer`, `CodeBlock` are placed in `features/chat/` but imported directly by `features/agents/`. They are not promoted to `components/` because they are AI-explainability concerns, not pure UI primitives.

### Folder Additions

```
features/
  chat/
  retrieval/
  engineering/
services/
  chatService.ts
  retrievalService.ts
  engineeringService.ts
types/
  chat.ts
  retrieval.ts
  engineering.ts
```

### State Management

- **Zustand** — `chatStore`: `messages[]`, `activeMode`, `isStreaming`, `lastMetadata`. Messages are the source of truth for displayed conversation.
- **React Query** — `useMutation` for all chat/ask, engineering, retrieval calls. On success, append response to `chatStore.messages`.
- **React Hook Form** — chat input form, debug form (error_message + stack_trace), PR review form.

### Routing

| Route | Component |
|---|---|
| `/chat` | `ChatPage` |
| `/retrieval` | `RetrievalExplainPage` |
| `/engineering` | `EngineeringCopilotPage` |

### Accessibility

- Chat input: `aria-label="Ask a question"`, `Enter` to send, `Shift+Enter` for newline.
- Message list: `role="log"`, `aria-live="polite"` for new messages.
- Citations panel: always visible (not collapsed by default). Keyboard operable expand/collapse per citation.
- Confidence badge: numeric value + text label — not color-only.
- Graph path: linearized as `<ol>` (ordered list) alongside visual breadcrumb.
- Loading state: `aria-busy="true"` on message list, `aria-live` announcement "Thinking...".
- Code block copy button: `aria-label="Copy code"`, success state announced.

### Markdown Rendering Security

`MarkdownRenderer` must use **react-markdown** with **rehype-sanitize**. The sanitize schema must allow only: `p`, `a`, `code`, `pre`, `strong`, `em`, `ul`, `ol`, `li`, `h1`–`h6`, `blockquote`. Strip all `script`, `style`, `iframe`, and event handler attributes. This is a security-critical component.

### Security

- All AI response content sanitized through `rehype-sanitize` before rendering.
- No `dangerouslySetInnerHTML` anywhere in chat components.
- `suggested_actions` are rendered as buttons — not as links with `href` from the API response (XSS vector).
- Citations memory content rendered as plain text only.

### Testing Checklist

- [ ] `ChatPage`: sends message, displays response with all explainability fields (MSW mock)
- [ ] `CitationPanel`: renders citation list with title, type, score
- [ ] `ConfidenceBadge`: renders correct color for high (>0.75), medium (0.5–0.75), low (<0.5)
- [ ] `MarkdownRenderer`: renders safe markdown; strips script tags
- [ ] `CodeBlock`: renders code with copy button; copy fires clipboard write
- [ ] `chatStore`: appends messages correctly; maintains conversation order
- [ ] `ChatInput`: Enter submits, Shift+Enter adds newline
- [ ] Empty state when chat history is empty
- [ ] Error state when API returns 500

### Performance

- Message list uses virtualization (`react-window`) if conversation exceeds 50 messages.
- `MarkdownRenderer` is memoized — does not re-render unchanged messages.
- Citations panel renders lazily — only builds DOM when panel is visible.
- `CodeBlock` uses dynamic import for syntax highlighter.

### Validation Checklist

- [ ] Chat sends question and displays answer with all 5 explainability fields
- [ ] Hybrid mode toggle is functional and changes retrieval behavior
- [ ] Citations render memory title, type, vector score, graph score
- [ ] Confidence badge renders correct numeric value and color band
- [ ] Graph path renders as ordered breadcrumb
- [ ] Participating agents list renders for multi-agent responses
- [ ] Suggested actions render as clickable buttons
- [ ] Retrieval explain page shows per-result score breakdown
- [ ] Engineering chat, debug, and PR review each produce a formatted response
- [ ] Markdown renders headings, code blocks, lists correctly
- [ ] Code blocks have working copy button

---

## Milestone 8.5 — Multi-Agent Workspace

### Goal

Build the multi-agent UI: agent registry browser, workflow dry-run planner, workflow execution view, Repository Agent panel, Debug Agent panel, and conversation history with per-turn agent attribution. All AI response explainability fields (shared from 8.4) are displayed on every response.

### LangGraph Portability

The workflow execution UI maps cleanly to LangGraph concepts:
- **Agent registry** = LangGraph node catalog.
- **Dry-run plan** = LangGraph `get_graph()` output (node + edge list).
- **Workflow timeline** = LangGraph execution step log.
- **Agent attribution** = LangGraph `metadata.source_node`.

When the backend migrates to LangGraph, only `agentsService.ts` changes — the UI components remain identical because they consume normalized workflow step objects.

### Features

- Agent registry grid: one card per agent, showing name, description, capabilities
- Workflow panel: question input + agent multi-select + metadata fields
- Dry-run planner: submit to `/workflow/plan`, display planned steps before execution
- Workflow execution: submit to `/workflow/run`, show response with full explainability
- Workflow execution timeline (ordered step list from response)
- Repository Agent panel: search input, branch selector, answer + commit summary list
- File history lookup: path input → commit list
- Debug Agent panel: error message + stack trace input → incident analysis + root cause
- Conversation history: session-persisted turns with per-turn agent attribution
- Execution metrics: response time badge per workflow run
- All AI responses show: participating_agents, citations, graph_path, confidence, retrieval_mode, suggested_actions

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/agents/` | List agents |
| `GET /api/v1/agents/{name}` | Agent detail |
| `POST /api/v1/agents/workflow/plan` | Dry-run |
| `POST /api/v1/agents/workflow/run` | Execute |
| `POST /api/v1/agents/repository/search` | Repository search |
| `GET /api/v1/agents/repository/branches` | Branch list |
| `POST /api/v1/agents/repository/file-history` | File history |
| `POST /api/v1/agents/debug/analyze` | Debug analysis |

### React Components

| Component | Location |
|---|---|
| `AgentsPage` | `features/agents/AgentsPage.tsx` |
| `AgentRegistryGrid` | `features/agents/AgentRegistryGrid.tsx` |
| `AgentCard` | `features/agents/AgentCard.tsx` |
| `WorkflowPanel` | `features/agents/WorkflowPanel.tsx` |
| `WorkflowPlanPreview` | `features/agents/WorkflowPlanPreview.tsx` |
| `WorkflowTimeline` | `features/agents/WorkflowTimeline.tsx` |
| `RepositoryAgentPanel` | `features/agents/RepositoryAgentPanel.tsx` |
| `BranchSelector` | `features/agents/BranchSelector.tsx` |
| `CommitSummaryList` | `features/agents/CommitSummaryList.tsx` |
| `DebugAgentPanel` | `features/agents/DebugAgentPanel.tsx` |
| `ParsedTraceView` | `features/agents/ParsedTraceView.tsx` |
| `ConversationHistoryList` | `features/agents/ConversationHistoryList.tsx` |
| `ConversationTurn` | `features/agents/ConversationTurn.tsx` |
| `ExecutionMetricsBadge` | `features/agents/ExecutionMetricsBadge.tsx` |

*Reused from 8.4:* `CitationPanel`, `ConfidenceBadge`, `RetrievalModeTag`, `GraphPathBreadcrumb`, `ParticipatingAgentsList`, `SuggestedActionsBar`, `MarkdownRenderer`.

### Folder Additions

```
features/
  agents/
services/
  agentsService.ts
types/
  agents.ts
```

### State Management

- **React Query** — `useQuery(['agents'])` for registry. `useMutation` for workflow/plan, workflow/run, repository search, debug analyze.
- **Zustand** — `agentStore`: `activePanel`, `selectedAgentName`, `workflowHistory[]`.
- **React Hook Form** — workflow form, repository search form, debug form.

### Routing

| Route | Component |
|---|---|
| `/agents` | `AgentsPage` with tab navigation |
| `/agents/workflow` | `WorkflowPanel` (tab within `AgentsPage`) |
| `/agents/repository` | `RepositoryAgentPanel` (tab) |
| `/agents/debug` | `DebugAgentPanel` (tab) |

### Accessibility

- Agent capability badges: text labels, not icons only.
- Workflow plan preview: `aria-label="Dry run plan"`, clearly marked with a "Preview only — not executed" label.
- Conversation history: `role="log"`, each turn has visible agent name text.
- Stack trace `<textarea>`: `aria-label="Stack trace"`, `spellcheck="false"`, monospace font.
- Suggested actions: rendered as `<button>` elements — never as plain text.
- Dry-run/execute distinction is communicated textually, not color-only.

### Security

- `suggested_actions` rendered as buttons only — not as anchor `href` from API response.
- Stack trace content is plain text input — never rendered as HTML.
- Agent names from registry displayed as text — not interpolated into URLs or API calls without validation.

### Testing Checklist

- [ ] `AgentRegistryGrid`: loads and displays agent cards with MSW mock
- [ ] `WorkflowPanel`: dry-run returns plan preview; execute returns full response
- [ ] `WorkflowTimeline`: renders planned steps as ordered list
- [ ] `RepositoryAgentPanel`: search returns answer + commit list
- [ ] `DebugAgentPanel`: stack trace input produces incident analysis
- [ ] `ConversationHistoryList`: turns rendered with agent attribution
- [ ] All explainability fields rendered (citations, confidence, graph path, mode, agents)
- [ ] Empty state when no agents registered
- [ ] Error state on API failure

### Performance

- Agent registry is prefetched after login (`staleTime: 5min`).
- Workflow history is capped at last 20 turns in `agentStore` to prevent memory growth.
- `ParsedTraceView` uses virtualized list for large stack traces.

### Validation Checklist

- [ ] Agent registry loads agent cards with capabilities
- [ ] Dry-run returns plan before execution
- [ ] Workflow run returns full response with all 6 explainability fields
- [ ] Repository search returns answer and commit summaries
- [ ] Branch list loads
- [ ] File history returns commit list
- [ ] Debug Agent parses stack trace and returns incidents
- [ ] Conversation history shows per-turn agent attribution
- [ ] Suggested actions are rendered and clickable
- [ ] Loading and error states exist for every panel

---

## Milestone 8.6 — Final Integration & QA

### Goal

Validate the complete application end-to-end. Run full test suite. Perform accessibility audit. Validate performance budgets. Complete the development journal.

### Features

- Full test suite run (Vitest + RTL + MSW)
- Playwright E2E smoke tests (login → dashboard → chat → agents)
- Lighthouse accessibility audit (target score: ≥ 90)
- Bundle size analysis (`vite-bundle-visualizer`)
- Responsive validation on desktop (1440px), laptop (1280px), tablet (768px)
- Fix all console warnings and TypeScript errors
- Development journal entry for Sprint 8
- README update with frontend setup instructions

### Validation Checklist

- [ ] All Vitest tests pass with no failures
- [ ] No TypeScript errors (`tsc --noEmit`)
- [ ] No ESLint errors or warnings
- [ ] Lighthouse accessibility score ≥ 90
- [ ] Bundle size < 500KB initial chunk
- [ ] All 6 milestones' validation checklists fully checked
- [ ] Sprint 8 journal entry written
- [ ] README updated with frontend setup steps

---

## Frontend Security Standards

| Area | Policy | Risk |
|---|---|---|
| JWT storage | localStorage (SPA trade-off; document risk) | Medium |
| Authorization headers | Injected by Axios interceptor; never hardcoded | Low |
| XSS prevention | All user content rendered as text; AI content through rehype-sanitize | High (mitigated) |
| Markdown sanitization | rehype-sanitize with strict allow-list schema | High (mitigated) |
| Suggested actions | Always rendered as `<button>` — never as `href` from API | High (mitigated) |
| Error boundaries | `ErrorBoundary` wraps each feature route | Low |
| API secrets | Only `VITE_API_BASE_URL` in env; never expose backend secrets | High |
| Sensitive logging | Token and user data never logged to console | Medium |
| Route protection | `AuthGuard` on all routes except `/login` | Medium |
| Input validation | React Hook Form + Zod schemas on all forms | Medium |

---

## Accessibility Standards (WCAG 2.1 AA)

| Requirement | Implementation |
|---|---|
| Keyboard navigation | All interactive elements reachable and operable via keyboard |
| Focus management | Dialogs/drawers trap focus; return focus on close |
| Screen reader support | Semantic HTML throughout; no div-soup |
| ARIA labels | All icon-only controls have `aria-label` |
| Accessible dialogs | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| Graph fallback | `EntityFallbackTable` always available as accessible alternative |
| Accessible tables | `<th scope="col">` on all headers |
| Reduced motion | All Framer Motion animations check `useReducedMotion()` |
| Color contrast | All text meets 4.5:1 ratio; UI elements meet 3:1 |
| Live regions | Chat message list and loading states use `aria-live` |
| Error messages | Linked to inputs via `aria-describedby` |
| Status indicators | Never communicated by color alone |

---

## Frontend Testing Strategy

### Stack

- **Vitest** — unit and component tests
- **React Testing Library** — component rendering and interaction
- **MSW (Mock Service Worker)** — API layer mocking (no real network calls in tests)
- **Playwright** — E2E smoke tests (Milestone 8.6)

### Per-Milestone Test Requirements

| Milestone | Components | Hooks | Stores | Services |
|---|---|---|---|---|
| 8.0 | Snapshot each primitive | — | — | — |
| 8.1 | LoginPage, AuthGuard, HealthWidget | useLogin, useAuth | authStore persist/restore | authService mock |
| 8.2 | MemoryTable, CreateMemoryDialog | useMemory, usePagination | workspaceStore | memoryService mock |
| 8.3 | GraphFilterBar, EntityFallbackTable | — | graphStore | entityService mock |
| 8.4 | CitationPanel, ConfidenceBadge, MarkdownRenderer | — | chatStore | chatService mock |
| 8.5 | AgentCard, WorkflowTimeline, DebugAgentPanel | — | agentStore | agentsService mock |

### Rules

- Every form has a validation test (valid submit + invalid submit paths).
- Every list component has: renders with data, renders empty state, renders error state.
- Every mutation has: success path (cache invalidated), error path (error state shown).
- Accessibility test on every modal/dialog (focus management, ESC behavior).
- Never mock `authStore` state directly in component tests — use `msw` to mock the login endpoint and run the real store.

---

## Performance Architecture

| Rule | Implementation |
|---|---|
| Route lazy loading | All routes use `React.lazy()` + `<Suspense>` |
| Suspense boundaries | One per feature route; shows `LoadingState` |
| Code splitting | Vite automatic chunk splitting per lazy route |
| Memoization | `React.memo` on list item components; `useCallback` on handlers |
| React Flow optimization | `nodesDraggable: false`, lazy neighbor loading, 500-node cap |
| Table virtualization | `react-window` for lists > 100 items |
| Search debounce | 300ms on all search inputs |
| Bundle optimization | Individual Lucide + Shadcn imports; no barrel files |
| Image optimization | SVG assets only; no raster images in UI |
| Query cancellation | AbortController signals on all list queries |

---

## Sprint Dependency Graph

```
8.0 Frontend Foundation
  ↓ (provides: api.ts, queryClient, design system, all UI primitives)
8.1 Authentication & Dashboard
  ↓ (provides: authStore, AppShell, AuthGuard, org_id injection)
  ├── 8.2 Memory Workspace ─────────────────────────────────────┐
  └── 8.3 Knowledge Graph  (parallel with 8.2, no dependency)   │
                                                                  ↓
                                                         8.4 AI Chat & Explainability
                                                           (depends on: 8.1 always,
                                                            benefits from: 8.2 for memory)
                                                                  ↓
                                                         8.5 Multi-Agent Workspace
                                                           (reuses: CitationPanel,
                                                            ConfidenceBadge, GraphPathBreadcrumb
                                                            from 8.4)
                                                                  ↓
                                                         8.6 Final Integration & QA
```

### Blocking Dependencies

- `8.0` → blocks all milestones (design system, api client)
- `8.1` → blocks all milestones (authStore, AppShell, AuthGuard)
- `8.4` → blocks `8.5` (shared explainability components)

### Parallel Opportunities

- `8.2 Memory Workspace` and `8.3 Knowledge Graph` can run in parallel after 8.1 completes.
- `8.3` has zero dependency on `8.2`.

### Shared Components Reuse Map

| Component | Produced in | Reused in |
|---|---|---|
| All UI primitives (Button, Card, Dialog, Table, Badge, etc.) | 8.0 | All |
| EmptyState, LoadingState, ErrorState, Skeleton | 8.0 | All |
| api.ts, queryClient.ts | 8.0 | All |
| authStore, AppShell, AuthGuard | 8.1 | All |
| CitationPanel, ConfidenceBadge | 8.4 | 8.5 |
| RetrievalModeTag, GraphPathBreadcrumb | 8.4 | 8.5 |
| ParticipatingAgentsList, SuggestedActionsBar | 8.4 | 8.5 |
| MarkdownRenderer, CodeBlock | 8.4 | 8.5 |

---

## Sub-Tasks

### Sub-Task 8.0 — Frontend Foundation
- **Intent:** Bootstrap Vite + React + TypeScript project, configure Tailwind with design tokens, initialize Shadcn, build all UI primitives, set up test infrastructure.
- **Expected Outcomes:** `npm run dev` starts. `npm run build` passes TypeScript. All UI primitives have snapshot tests. Design tokens visible in browser DevTools.
- **Status:** [ ] pending

### Sub-Task 8.1 — Authentication & Dashboard
- **Intent:** Implement login, JWT storage, AuthGuard, AppShell layout, and Dashboard with live backend health/stats widgets.
- **Expected Outcomes:** Login → Dashboard flow works. AuthGuard redirects unauthenticated users. All 6 dashboard widgets render live data.
- **Status:** [ ] pending

### Sub-Task 8.2 — Memory Workspace
- **Intent:** Build memory entry list, search, create dialog, scenario navigation, and memory detail drawer.
- **Expected Outcomes:** Memory entries load, paginate, and are searchable. CRUD operations complete with cache invalidation. Scenario filter works.
- **Status:** [ ] pending

### Sub-Task 8.3 — Knowledge Graph Viewer
- **Intent:** Build interactive entity/relationship graph with React Flow, inspector panels, filter chips, and accessible fallback table.
- **Expected Outcomes:** Graph renders entities and relationships. Node click opens inspector. Filter chips work. Fallback table available.
- **Status:** [ ] pending

### Sub-Task 8.4 — AI Chat & Explainability Workspace
- **Intent:** Build RAG chat interface with all 6 explainability fields always visible, plus retrieval explain view and engineering copilot panel.
- **Expected Outcomes:** Chat sends messages and displays answers with citations, confidence, graph path, retrieval mode, participating agents, suggested actions. Markdown renders safely.
- **Status:** [ ] pending

### Sub-Task 8.5 — Multi-Agent Workspace
- **Intent:** Build agent registry, workflow dry-run + execution, repository agent panel, debug agent panel, conversation history with attribution.
- **Expected Outcomes:** All agent endpoints integrated. Workflow plan preview works before execution. All explainability fields from 8.4 reused.
- **Status:** [ ] pending

### Sub-Task 8.6 — Final Integration & QA
- **Intent:** Full test suite, accessibility audit, bundle analysis, responsive validation, journal entry.
- **Expected Outcomes:** All tests pass. No TypeScript errors. Lighthouse accessibility ≥ 90. Bundle < 500KB initial.
- **Status:** [ ] pending
