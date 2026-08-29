# Sprint 8 — Frontend AI Workspace: Final Implementation Blueprint

> **Status:** Architecture Frozen. This document is the official Sprint 8 implementation blueprint.
> Do not modify architecture without a recorded decision. Append implementation notes at the bottom of each milestone section.

---

## Overview

Sprint 8 builds the TeamMemoryOS web frontend from scratch using React 18, TypeScript, Vite, Tailwind CSS, Shadcn UI, React Query v5, Zustand v4, React Router v6, React Hook Form v7, React Flow, and Framer Motion. The frontend surfaces all backend capabilities from Sprints 1–7 as a premium desktop-first AI Operating System interface.

The `frontend/` folder exists with empty subdirectories. No React scaffolding has been written yet. Every milestone builds on prior milestones in strict dependency order.

---

## Milestone Order

```
8.0 Frontend Foundation           ← Infrastructure. Blocks everything.
  ↓
8.1 Authentication & Dashboard    ← Auth shell + live dashboard widgets.
  ↓
8.2 Memory Workspace              ← Memory CRUD, search, scenarios.
  ↓ (parallel opportunity)
8.3 Knowledge Graph               ← Entity/relationship graph. Parallel with 8.2.
  ↓
8.4 AI Chat & Explainability      ← RAG chat, explainability, Engineering Copilot.
  ↓
8.5 Multi-Agent Workspace         ← Agent registry, workflow timeline, debug/repo panels.
  ↓
8.6 Final Integration & QA        ← E2E audit, accessibility, performance, release.
```

**Strict sequential chain:** `8.0 → 8.1 → 8.2 → 8.4 → 8.5 → 8.6`
**Parallel opportunity:** `8.2 ‖ 8.3` (no inter-dependency after 8.1)

---

## Enterprise Folder Structure

This is the frozen canonical folder layout. Every developer and every Bob agent must respect folder responsibilities.

```
frontend/
  app/                  ← React Router route tree only. No business logic.
    index.tsx           ← Router root, lazy route registry
    routes.tsx          ← Route definitions with React.lazy() wrappers

  providers/            ← Global React context providers. Initialization only.
    ThemeProvider.tsx
    QueryProvider.tsx
    AuthProvider.tsx
    TooltipProvider.tsx
    MotionProvider.tsx
    index.tsx           ← Ordered provider composition

  layouts/              ← Full-page structural wrappers. One per surface.
    RootLayout.tsx      ← Root error boundary + top-level Suspense
    WorkspaceLayout.tsx ← Authenticated shell: Sidebar + Topbar + content
    AuthLayout.tsx      ← Unauthenticated surface: centered card layout
    ErrorLayout.tsx     ← Unrecoverable error surface (boundary fallback)
    SettingsLayout.tsx  ← Settings panel layout (future)

  config/               ← Static application configuration. No runtime logic.
    navigation.ts       ← Single source of truth: nav items, icons, routes, permissions
    theme.ts            ← Design token exports for JS consumers
    constants.ts        ← App-wide constants (pagination defaults, debounce ms)

  components/           ← Reusable design system primitives only.
    ui/                 ← Shadcn-based components with project token overrides
    feedback/           ← LoadingState, EmptyState, ErrorState, Skeleton, Spinner

  features/             ← Self-contained feature modules. One directory per domain.
    auth/               ← LoginPage, useLogin
    dashboard/          ← DashboardPage, widgets
    memory/             ← MemoryPage, MemoryTable, CreateMemoryDialog
    scenarios/          ← ScenarioList, CreateScenarioDialog
    graph/              ← KnowledgeGraphPage, GraphCanvas, inspectors
    chat/               ← ChatPage, ChatMessageList, ChatInput
    retrieval/          ← RetrievalExplainPage, RetrievalResultCard
    engineering/        ← EngineeringCopilotPage, DebugPanel, PRReviewPanel
    agents/             ← AgentsPage, WorkflowTimeline, RepositoryAgentPanel
    explainability/     ← ALL shared AI explainability components (see §5)

  services/             ← All API calls. One exported function per endpoint.
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
    usersService.ts

  stores/               ← Zustand stores. Client UI state only. Never server data.
    authStore.ts
    uiStore.ts
    workspaceStore.ts
    graphStore.ts
    chatStore.ts
    agentStore.ts

  hooks/                ← Reusable custom hooks shared across features.
    useAuth.ts
    usePagination.ts
    useDebounce.ts
    useOrganization.ts

  lib/                  ← Low-level configuration instances.
    api/
      client.ts         ← Single Axios instance
      interceptors.ts   ← Request + response interceptor registration
      auth.ts           ← JWT injection logic
      organization.ts   ← X-Organization-ID injection logic
      errors.ts         ← Error normalization → ApiError
    queryClient.ts      ← React Query client with global defaults

  utils/                ← Pure functions. No React. No side effects.
    formatDate.ts
    truncate.ts
    colorFromType.ts
    scoreToLabel.ts
    cn.ts               ← Tailwind class merge utility

  styles/               ← Global CSS and design tokens.
    globals.css
    tokens.css          ← CSS custom property design token definitions

  types/                ← Shared TypeScript interfaces mirroring backend schemas.
    api.ts              ← ApiError, PaginatedResponse, base types
    auth.ts
    memory.ts
    scenario.ts
    entity.ts
    relationship.ts
    chat.ts
    retrieval.ts
    engineering.ts
    agents.ts

  assets/               ← Static assets: logos, icons, images.
  index.html
  main.tsx
  vite.config.ts
  tailwind.config.ts
  tsconfig.json
  package.json
  .env.example
```

### Folder Responsibility Table

| Folder | Owns | Never contains |
|---|---|---|
| `app/` | Route definitions + lazy imports | Business logic, API calls, state |
| `providers/` | Provider initialization + composition order | Feature logic, UI rendering |
| `layouts/` | Structural page wrappers, slot areas | Feature data, API calls |
| `config/` | Static configuration objects | Runtime logic, React components |
| `components/ui/` | Design system primitives | API calls, business logic, store reads |
| `components/feedback/` | Loading, empty, error, skeleton states | Feature-specific content |
| `features/` | Feature pages + feature-local components | Direct `fetch()` / `axios` / `useAxios` |
| `features/explainability/` | AI explainability display components | Chat logic, agent orchestration |
| `services/` | One typed function per API endpoint | React components, hooks, stores |
| `stores/` | Client UI state + session state | Server response lists, loading flags |
| `hooks/` | Reusable hook logic shared across features | Component JSX |
| `lib/api/` | Axios client + interceptor modules | Feature logic, store reads |
| `utils/` | Pure helper functions | React, side effects, imports |
| `types/` | TypeScript interface definitions | Runtime logic, default values |

---

## Providers Architecture

Providers are initialized in `providers/index.tsx` in a strict composition order. Order matters — each provider may depend on those above it.

```
1. ThemeProvider    ← CSS variable application; no dependencies
2. MotionProvider   ← Framer Motion reduced-motion detection; no dependencies
3. TooltipProvider  ← Radix tooltip root; no dependencies
4. QueryProvider    ← React Query client; no dependencies
5. AuthProvider     ← Reads authStore; must be inside QueryProvider for prefetch
```

**Rules:**
- No provider reads from another provider's context.
- Providers do not render any UI — they only inject context.
- `AuthProvider` handles session restore from localStorage on mount and triggers post-login prefetch. It is not responsible for redirect logic — that belongs in `AuthGuard`.
- The composition entry point is `providers/index.tsx`, exported as `<AppProviders>`, mounted once in `main.tsx`.

---

## Layout Architecture

Five layouts cover every surface in the application.

| Layout | Route surface | Owns | Notes |
|---|---|---|---|
| `RootLayout` | All routes | Root `<ErrorBoundary>`, global `<Suspense>` fallback | Renders `<Outlet>` |
| `WorkspaceLayout` | All authenticated routes | `Sidebar`, `Topbar`, main content slot | Requires auth |
| `AuthLayout` | `/login` | Centered card container | No auth required |
| `ErrorLayout` | Error boundary fallback | Full-screen error message + retry | Used by `RootLayout` on uncaught error |
| `SettingsLayout` | `/settings/*` (future) | Split-panel settings shell | Planned, not in Sprint 8 scope |

`WorkspaceLayout` renders `Sidebar` and `Topbar`. It does **not** own navigation data — navigation items are read from `config/navigation.ts`.

---

## Navigation Configuration

`config/navigation.ts` is the single source of truth for all navigation concerns. It exports a typed `NavItem[]` array used by:

- `Sidebar` — renders nav items with icons and active state
- `Topbar` — renders breadcrumbs
- `WorkspaceLayout` — derives route-level permissions
- Future command palette — searches nav items by label

Each `NavItem` has the shape:

```typescript
interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  section: 'primary' | 'tools' | 'admin';
  requiredPermission?: string;   // future role-based gating
  badge?: string;                // future notification count
}
```

Navigation items are **never** hardcoded inside `Sidebar.tsx`. All changes to the nav go through `config/navigation.ts`.

---

## Design System Architecture

### Color Palette (`styles/tokens.css`)

```css
:root {
  /* Backgrounds */
  --color-bg-base:       #0a0a0f;
  --color-bg-surface:    #111118;
  --color-bg-elevated:   #1a1a24;
  --color-bg-subtle:     #22222f;

  /* Brand — Indigo */
  --color-brand:         #6366f1;
  --color-brand-hover:   #818cf8;
  --color-brand-muted:   #312e81;

  /* Semantic */
  --color-success:       #22c55e;
  --color-warning:       #f59e0b;
  --color-danger:        #ef4444;
  --color-info:          #38bdf8;

  /* Text */
  --color-text-primary:  #f1f5f9;
  --color-text-secondary:#94a3b8;
  --color-text-muted:    #475569;

  /* Borders */
  --color-border:        #1e1e2e;
  --color-border-focus:  #6366f1;

  /* Confidence banding (AI explainability) */
  --color-conf-high:     #22c55e;   /* score > 0.75 */
  --color-conf-med:      #f59e0b;   /* score 0.5–0.75 */
  --color-conf-low:      #ef4444;   /* score < 0.5 */
}
```

### Typography

- Body: `Inter`, 1rem/400
- Code: `JetBrains Mono`, 0.875rem/400
- Scale: xs(0.75) · sm(0.875) · base(1) · lg(1.125) · xl(1.25) · 2xl(1.5) · 3xl(1.875)

### Spacing

4px base unit. All spacing uses Tailwind's default 4px grid.

### Shadows / Elevation

```css
--shadow-sm:   0 1px 2px rgba(0,0,0,0.4);
--shadow-md:   0 4px 12px rgba(0,0,0,0.5);
--shadow-lg:   0 8px 24px rgba(0,0,0,0.6);
--shadow-glow: 0 0 20px rgba(99,102,241,0.2);
```

### Animation Rules (Framer Motion)

- All animations check `useReducedMotion()` from Framer Motion.
- Page entrance: opacity 0→1, y +8px→0, 200ms easeOut.
- Panel slide-in: x +16px→0, 180ms easeOut.
- Skeleton: CSS `animate-pulse` only — no JS animation.
- Data tables: no animation — only skeleton during loading.

### Component Library (`components/ui/`)

| Component | Purpose |
|---|---|
| `Button` | 4 variants (primary, secondary, ghost, destructive), loading state, icon slot |
| `Input` | Label, error message, hint text slots |
| `Card` | Surface container with header, body, footer slots |
| `Badge` | 6 semantic variants + confidence variant |
| `Dialog` | Modal with focus trap, ESC close, `aria-labelledby` |
| `Drawer` | Side panel with overlay and close button |
| `Table` | Accessible data table with `th scope` |
| `Tabs` | Keyboard-navigable tab group |
| `Tooltip` | Hover + focus disclosure for icon-only controls |
| `Dropdown` | Keyboard-operable menu |
| `Skeleton` | Shape-matched loading placeholder |
| `Spinner` | Inline loading indicator with `aria-label` |

**Rules:**
- Before creating a new UI element, check `components/ui/` first.
- Never define a color, shadow, or spacing value inline — always use CSS variables or Tailwind tokens.
- No component in `components/ui/` reads from any store or service.
- Components stay under 200 lines.

---

## Modular API Architecture (`lib/api/`)

The networking layer is split into five modules. No feature component ever imports Axios directly.

### `lib/api/client.ts`
Creates and exports the single Axios instance with `baseURL` from `VITE_API_BASE_URL`. Registers interceptors from `interceptors.ts` on startup.

### `lib/api/interceptors.ts`
Registers request and response interceptors on the Axios instance in order:
1. Request: `auth.ts` injects JWT
2. Request: `organization.ts` injects `X-Organization-ID`
3. Response: success passthrough
4. Response: error → `errors.ts` normalization

### `lib/api/auth.ts`
Request interceptor that reads `access_token` from `authStore` and attaches `Authorization: Bearer <token>` to every outbound request.

### `lib/api/organization.ts`
Request interceptor that reads `organization_id` from `authStore` and attaches `X-Organization-ID` header. Requests that do not require org context (login, health) are not affected — the header is ignored by those endpoints.

### `lib/api/errors.ts`
Response interceptor that catches all Axios errors and normalizes them into a typed `ApiError` object:
```typescript
interface ApiError {
  message: string;
  status: number;
  code?: string;
}
```
On HTTP 401 → clears `authStore` and redirects to `/login`. Raw Axios errors never propagate to feature code.

**Request Cancellation:**
All list and search queries pass an `AbortController` signal via React Query's `signal` parameter to the service function. Mutations are never cancelled.

---

## React Query Architecture

React Query owns **all server state**. Zustand never holds API response data.

### Cache Key Convention

```
[resource, scope, ...filters]

['health']
['memory', orgId]
['memory', orgId, scenarioId]
['memory', 'detail', entryId]
['scenarios', orgId]
['entities', orgId]
['neighbors', entityId]
['agents']
['agents', 'detail', agentName]
```

### staleTime by Resource

| Resource | staleTime | Reason |
|---|---|---|
| Health | 30s | Must reflect live backend status |
| Memory entries | 60s | Low churn per session |
| Scenarios | 2min | Metadata rarely changes mid-session |
| Entities / Relationships | 2min | Graph stable within session |
| Agent registry | 5min | Static capability metadata |
| Chat / AI responses | `Infinity` | Mutation results; never re-fetched |

### Mutation Invalidation Rules

| Mutation | Invalidates |
|---|---|
| Create memory entry | `['memory', orgId]` |
| Create scenario | `['scenarios', orgId]` |
| Workflow run | Nothing — result appended to `chatStore` |

### Post-Login Prefetch

After successful login, prefetch in order:
1. `['health']`
2. `['scenarios', orgId]`
3. `['agents']`

This ensures Dashboard renders immediately without skeleton delays.

### Retry Policy

```typescript
retry: (failureCount, error) => {
  if ([401, 403, 404].includes(error.status)) return false;
  return failureCount < 2;
}
```

### Pagination

Default page size: 20. All list queries accept `{ page, limit }`. Use `keepPreviousData: true` to prevent table flash during page change. Use `useInfiniteQuery` for chat history and search result streams.

---

## Zustand Architecture

### Boundary Rule

Zustand holds **client UI state only**. The moment data comes from an API response, React Query owns it.

| Belongs in Zustand | Never in Zustand |
|---|---|
| JWT token, user, org_id | API response lists |
| Sidebar collapsed state | Loading / error flags for requests |
| Theme preference | Paginated data |
| Selected entity ID (not the entity data) | Form field values |
| Chat message history (assembled client-side) | React Query cache |
| Agent active panel tab | Server-generated IDs before creation |

### Store Definitions

| Store | State fields | Persistence |
|---|---|---|
| `authStore` | `access_token`, `user`, `organization_id` | localStorage via `persist` |
| `uiStore` | `sidebarCollapsed`, `theme`, `toasts[]` | localStorage (theme only) |
| `workspaceStore` | `activeSection`, `activeScenarioId` | Session only |
| `graphStore` | `selectedEntityId`, `expandedNodeIds[]`, `filterType`, `searchTerm` | Session only |
| `chatStore` | `messages[]`, `activeMode`, `isStreaming`, `abortController` | Session only |
| `agentStore` | `activePanel`, `selectedAgentName`, `workflowHistory[]` | Session only |

---

## `features/explainability/` — AI Explainability Feature Module

### Why a Dedicated Feature Module

AI explainability components are used across Chat, Retrieval Inspector, Engineering Copilot, Multi-Agent Workspace, and the future AI Governance Dashboard. If placed inside `features/chat/`, they become implicitly owned by chat and must be moved when reused. Placing them in `components/ui/` would be wrong — they are not design system primitives; they encode AI domain knowledge. A dedicated `features/explainability/` module makes the ownership explicit, the reuse path obvious, and the future governance dashboard a natural extension.

### Components

| Component | Responsibility |
|---|---|
| `CitationPanel` | Full citation list for an AI response |
| `CitationCard` | Single citation: title, type, vector score, graph score, rank |
| `ConfidenceBadge` | Numeric confidence value + color band (high/med/low) |
| `ConfidenceLegend` | Explains confidence banding — shown on first render or on hover |
| `GraphPathPanel` | Entity traversal chain rendered as breadcrumb + accessible `<ol>` |
| `RetrievalModeTag` | Tag showing: semantic / hybrid / engineering |
| `RetrievalReasonCard` | Single retrieval result with score breakdown (vector + graph + combined) |
| `SourceMemoryCard` | Memory entry preview: title, type, snippet, link |
| `ExplainabilityDrawer` | Collects all panels above into a slide-in drawer for full response inspection |

### Usage Rule

Every AI response surface **must** render:
1. `CitationPanel` — always visible, not collapsible by default
2. `ConfidenceBadge` — shown inline beside the answer
3. `RetrievalModeTag` — shown inline beside the answer
4. `GraphPathPanel` — shown below the answer when `graph_path` is non-empty
5. `ParticipatingAgentsList` — shown when `participating_agents` is non-empty

These components are **never hidden**. They are the proof of explainability required for the IBM AI Builders Challenge.

### Surfaces That Import from `features/explainability/`

- `features/chat/` — main RAG chat
- `features/retrieval/` — retrieval explain page
- `features/engineering/` — engineering copilot responses
- `features/agents/` — multi-agent workflow responses
- Future: `features/governance/` — AI usage audit dashboard

### Rule

`features/explainability/` components never call services or stores directly. They receive all data as props. They are pure display components.

---

## Milestone 8.0 — Frontend Foundation

### Why This Milestone Exists

All downstream milestones depend on:
- A working Vite + TypeScript build
- Tailwind CSS with the correct design token configuration
- Shadcn UI initialized with project overrides
- The global provider tree (`providers/index.tsx`) already assembled
- The Axios client fully configured with interceptors
- The React Query client with global defaults
- All 12 UI primitives and 3 feedback components available for import
- Vitest + RTL + MSW test infrastructure runnable

Without this milestone complete and validated, no feature milestone can be implemented correctly. A single misconfigured CSS variable or missing provider propagates as a bug into every downstream milestone. This milestone is **infrastructure**, not a feature.

### Goal

Bootstrap the Vite + React 18 + TypeScript project. Configure Tailwind + Shadcn with TeamMemoryOS design tokens. Assemble the global provider tree. Build all UI primitives. Set up the modular API layer structure. Set up test infrastructure.

### Features

- Vite + React 18 + TypeScript scaffold with strict mode
- Tailwind CSS with `tokens.css` design token system
- Shadcn UI initialized; components overridden with project tokens
- `providers/index.tsx` — ordered provider composition
- `layouts/RootLayout.tsx` — root error boundary + Suspense
- All `components/ui/` primitives (12 components)
- `components/feedback/` — LoadingState, EmptyState, ErrorState, Skeleton, Spinner
- `lib/api/` — modular API layer (5 modules, no auth wired yet)
- `lib/queryClient.ts` — React Query client with retry/staleTime defaults
- `utils/cn.ts` — Tailwind class merge utility
- `utils/` — formatDate, truncate, colorFromType, scoreToLabel
- `config/constants.ts` — PAGE_SIZE=20, DEBOUNCE_MS=300
- TypeScript path aliases: `@/` → `src/`
- `.env.example` with `VITE_API_BASE_URL`
- Vitest + React Testing Library + MSW installed and configured
- `package.json` with all dependencies pinned

### Backend APIs Required

**None.** This milestone has zero backend integration. It is purely frontend infrastructure.

### React Components

| Component | Location | Notes |
|---|---|---|
| `Button` | `components/ui/Button.tsx` | 4 variants, loading state, icon slot |
| `Input` | `components/ui/Input.tsx` | Label, error, hint slots |
| `Card` | `components/ui/Card.tsx` | Header, body, footer slots |
| `Badge` | `components/ui/Badge.tsx` | 6 semantic + confidence variants |
| `Dialog` | `components/ui/Dialog.tsx` | Focus trap, ESC, aria-labelledby |
| `Drawer` | `components/ui/Drawer.tsx` | Side panel with overlay |
| `Table` | `components/ui/Table.tsx` | th scope, keyboard rows |
| `Tabs` | `components/ui/Tabs.tsx` | Keyboard navigation |
| `Tooltip` | `components/ui/Tooltip.tsx` | Hover + focus disclosure |
| `Dropdown` | `components/ui/Dropdown.tsx` | Keyboard operable |
| `Skeleton` | `components/ui/Skeleton.tsx` | Shape-matched |
| `Spinner` | `components/ui/Spinner.tsx` | aria-label required |
| `EmptyState` | `components/feedback/EmptyState.tsx` | Icon, heading, optional CTA |
| `ErrorState` | `components/feedback/ErrorState.tsx` | Retry action |
| `LoadingState` | `components/feedback/LoadingState.tsx` | Full-panel skeleton grid |

### Folder Additions

```
frontend/
  app/index.tsx
  app/routes.tsx
  providers/
  layouts/RootLayout.tsx
  config/constants.ts
  config/theme.ts
  components/ui/          ← 12 primitives
  components/feedback/    ← 5 feedback components
  lib/api/                ← 5 modules (no auth interceptor wired yet)
  lib/queryClient.ts
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

### Accessibility

- All primitives ship with correct ARIA roles.
- `Dialog`: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`.
- `Button` loading state: uses `aria-disabled` (not `disabled`) to preserve focus.
- Color tokens verified to meet WCAG AA contrast (4.5:1 text, 3:1 UI elements).
- `Tabs`: arrow-key navigation per ARIA APG pattern.

### Security

- Strict TypeScript (`"strict": true`).
- No `dangerouslySetInnerHTML` in any primitive.
- `VITE_API_BASE_URL` is the only env variable. No secrets in build output.

### Testing Checklist

- [ ] Vitest, RTL, MSW installed and `npm test` runs
- [ ] Snapshot test for each of: Button, Card, Badge, Spinner, EmptyState
- [ ] All primitives render without console errors
- [ ] CSS variables resolve correctly in jsdom test environment

### Performance

- Shadcn components imported individually (no barrel imports).
- Lucide icons imported individually.
- Route components use `React.lazy()` from Milestone 8.1 onward.

### Validation Checklist

- [ ] `npm run dev` starts without errors
- [ ] `npm run build` completes with zero TypeScript errors
- [ ] `npm test` passes
- [ ] Design tokens visible in browser DevTools (CSS variables present on `:root`)
- [ ] Path alias `@/` resolves correctly in both app and test environments
- [ ] Tailwind purge configured for `frontend/src/**`

---

## Milestone 8.1 — Authentication & Dashboard

### Goal

Implement the complete authentication flow (login, logout, JWT storage, route guarding, session restore), build the `WorkspaceLayout` shell (Sidebar + Topbar driven by `config/navigation.ts`), and deliver the Dashboard with six live backend health and summary widgets.

### Features

- Login page with React Hook Form validation
- `authStore` with localStorage persistence via Zustand `persist`
- `AuthGuard` — redirects unauthenticated requests to `/login`
- `ProtectedRoute` — HOC wrapper for authenticated routes
- Logout: clears store + localStorage, redirects to `/login`
- Session restore on page refresh (reads token from localStorage on mount)
- Token refresh placeholder: `useTokenRefresh` hook exists but is a no-op pending backend endpoint
- `WorkspaceLayout` — Sidebar + Topbar + main content slot
- Sidebar navigation built from `config/navigation.ts`
- Topbar: organization name, user display, logout button
- Dashboard with six MVP widgets (details in widget table below)
- Post-login prefetch: health, scenarios, agents

### Dashboard Widgets (MVP)

| Widget | Backend API | Display |
|---|---|---|
| Backend Health | `GET /api/v1/health/` | Status indicator + latency ms |
| Database Health | `GET /api/v1/health/db` | Status indicator |
| Memory Count | `GET /api/v1/memory/organization/{org_id}` | Total entry count |
| Scenario Count | `GET /api/v1/scenarios/organization/{org_id}` | Total scenario count |
| Agent Count | `GET /api/v1/agents/` | Total registered agents |
| Quick Actions | Static | Shortcut links: Memory, Chat, Graph, Agents |

Analytics charts are deferred to Milestone 8.6.

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/login` | OAuth2 password → JWT |
| `GET /api/v1/health/` | Backend health widget |
| `GET /api/v1/health/db` | DB health widget |
| `GET /api/v1/memory/organization/{org_id}` | Memory count widget |
| `GET /api/v1/scenarios/organization/{org_id}` | Scenario count widget |
| `GET /api/v1/agents/` | Agent count widget + prefetch |

### React Components

| Component | Location |
|---|---|
| `LoginPage` | `features/auth/LoginPage.tsx` |
| `AuthGuard` | `components/auth/AuthGuard.tsx` |
| `ProtectedRoute` | `components/auth/ProtectedRoute.tsx` |
| `WorkspaceLayout` | `layouts/WorkspaceLayout.tsx` |
| `AuthLayout` | `layouts/AuthLayout.tsx` |
| `Sidebar` | `layouts/Sidebar.tsx` |
| `Topbar` | `layouts/Topbar.tsx` |
| `DashboardPage` | `features/dashboard/DashboardPage.tsx` |
| `HealthWidget` | `features/dashboard/HealthWidget.tsx` |
| `MemoryCountWidget` | `features/dashboard/MemoryCountWidget.tsx` |
| `ScenarioCountWidget` | `features/dashboard/ScenarioCountWidget.tsx` |
| `AgentCountWidget` | `features/dashboard/AgentCountWidget.tsx` |
| `QuickActionsWidget` | `features/dashboard/QuickActionsWidget.tsx` |

### Folder Additions

```
features/auth/
features/dashboard/
layouts/WorkspaceLayout.tsx
layouts/AuthLayout.tsx
layouts/Sidebar.tsx
layouts/Topbar.tsx
components/auth/
config/navigation.ts
services/authService.ts
services/healthService.ts
stores/authStore.ts
stores/uiStore.ts
hooks/useAuth.ts
hooks/useOrganization.ts
types/auth.ts
```

### State Management

- `authStore` (Zustand + persist): `access_token`, `user`, `organization_id`.
- `uiStore` (Zustand + persist for theme): `sidebarCollapsed`, `theme`.
- React Query: health queries `staleTime: 30s`; memory/scenario/agent counts prefetched.
- React Hook Form: login form.

### Routing

| Route | Layout | Component | Protected |
|---|---|---|---|
| `/login` | `AuthLayout` | `LoginPage` | No |
| `/` | `WorkspaceLayout` | `DashboardPage` | Yes |
| `/*` | `WorkspaceLayout` | Child route | Yes |

### Accessibility

- Login form: `<label>` per field, `aria-required`, `aria-describedby` for errors.
- Sidebar: `<nav role="navigation" aria-label="Main navigation">`, `aria-current="page"` on active item.
- Dashboard widgets: `role="region"` with `aria-labelledby` pointing to widget heading.
- Topbar logout button: `aria-label="Sign out"`.

### Security

- JWT stored in `localStorage` — documented risk, accepted for SPA.
- Token never logged to console or included in error messages.
- Logout clears `authStore` entirely and removes localStorage key.
- `AuthGuard` renders `null` until auth state is resolved (prevents flash of protected content).
- Login error: generic message — does not reveal whether email or password failed.

### Testing Checklist

- [ ] `useLogin`: success path stores token + redirects
- [ ] `useLogin`: failure path sets error message
- [ ] `AuthGuard`: renders children when authenticated; redirects when not
- [ ] `LoginPage`: invalid form shows validation errors; valid form calls service
- [ ] `authStore`: persistence to localStorage and restore on mount
- [ ] `DashboardPage`: all 6 widgets render with MSW-mocked API responses
- [ ] `HealthWidget`: green on healthy response; red on unhealthy/error

### Performance

- Dashboard widgets use parallel independent React Query queries.
- All routes except `/login` are `React.lazy()`.
- Sidebar is rendered eagerly (it is part of the persistent shell).

### Validation Checklist

- [ ] Login with valid credentials stores JWT and redirects to `/`
- [ ] Invalid credentials shows error without field-level disclosure
- [ ] Unauthenticated `/` redirects to `/login`
- [ ] Logout clears session and redirects to `/login`
- [ ] Page refresh restores authenticated session
- [ ] All 6 dashboard widgets display live data
- [ ] Sidebar highlights active route correctly
- [ ] Sidebar collapses and expands

---

## Milestone 8.2 — Memory Workspace

### Goal

Build the organizational memory interface: paginated table of memory entries filtered by scenario, semantic search, create/view entries via a detail drawer with deep-link URL support, scenario navigation, and memory link display.

### Features

- Memory entry table with pagination (20 per page)
- Scenario sidebar navigation (filter table by selected scenario)
- Semantic search with 300ms debounce
- Memory entry detail Drawer — opens on row click
- Deep-link support: route `/memory/:memoryId` opens drawer directly on load
- "Copy Link" button in drawer header
- Create memory entry dialog
- Create scenario dialog
- Memory type badge (DECISION, CODE, DISCUSSION, DOCUMENTATION, INCIDENT)
- Memory link list in drawer detail
- Bulk action scaffolding (checkboxes present, action bar disabled — future-ready)
- Empty state, error state, loading skeleton

### Deep-Link Routing Behavior

The memory detail Drawer is the primary UX (row click → drawer). However, the URL is updated to `/memory/:memoryId` when a drawer opens. This enables:
- Sharing a direct link to a memory entry
- Browser back button closes the drawer (React Router location state)
- Citations from AI responses can link directly to a memory entry

On direct navigation to `/memory/:memoryId`, the Drawer opens immediately after the list loads. The list remains visible behind the drawer so context is preserved.

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
| `CreateScenarioDialog` | `features/scenarios/CreateScenarioDialog.tsx` |

### Folder Additions

```
features/memory/
features/scenarios/
services/memoryService.ts
services/scenarioService.ts
types/memory.ts
types/scenario.ts
stores/workspaceStore.ts
```

### State Management

- React Query: `['memory', orgId]`, `['memory', orgId, scenarioId]`, `['memory', 'detail', entryId]`, `['scenarios', orgId]`.
- React Query mutation: create memory → invalidate `['memory', orgId]`; create scenario → invalidate `['scenarios', orgId]`.
- Zustand `workspaceStore.activeScenarioId`: which scenario is selected in sidebar.
- React Hook Form: `CreateMemoryDialog`, `CreateScenarioDialog`.

### Routing

| Route | Behavior |
|---|---|
| `/memory` | List page, no drawer |
| `/memory/:memoryId` | List page + Drawer open for `memoryId` |
| `/scenarios` | Scenario list (renders within `MemoryPage` sidebar) |

### Accessibility

- Table: `<th scope="col">` on all headers. Row `onClick` opens drawer — not navigation.
- Search: `role="search"`, `aria-label="Search memory entries"`.
- Drawer: `role="complementary"`, `aria-label="Memory entry detail"`. Focus moves to drawer heading on open; returns to triggering row on close.
- Memory type badges: text label + color (not color-only).
- Bulk checkboxes: `aria-label="Select entry"`, `aria-disabled="true"` in current phase.

### Security

- `org_id` injected by Axios interceptor — never read from URL parameters.
- Memory entry content rendered as plain text — no HTML rendering of user-generated content.

### Testing Checklist

- [ ] `MemoryTable` renders list with MSW mock; shows skeleton while loading
- [ ] `MemorySearchBar` debounce: query fires after 300ms, not on every keystroke
- [ ] `CreateMemoryDialog` validates required fields; success invalidates cache
- [ ] Deep-link: navigating to `/memory/:id` opens drawer with correct entry
- [ ] "Copy Link" writes correct URL to clipboard
- [ ] Empty state on empty array response; error state on 500

### Performance

- `keepPreviousData: true` during page changes — no table flash.
- `MemoryEntryDrawer` DOM not inserted until first open.
- Memory entry content truncated at 200 characters in table row.

### Validation Checklist

- [ ] Memory list loads and paginates
- [ ] Scenario filter correctly scopes the memory list
- [ ] Semantic search returns results or empty state
- [ ] Create memory form submits and list refreshes
- [ ] Drawer opens on row click and on direct URL navigation
- [ ] Copy Link works
- [ ] Loading skeletons appear during API calls
- [ ] Error state on API failure

---

## Milestone 8.3 — Knowledge Graph Viewer

### Goal

Build an interactive knowledge graph visualization using React Flow. Progressive loading architecture: initial entity set, on-demand neighbor expansion, entity type filtering, full-text entity search, entity and relationship inspectors, mini-map, zoom controls, and an accessible table fallback.

### Progressive Loading Architecture

The graph does not load all edges upfront. This prevents performance degradation on large organizations.

| Phase | Data loaded | Trigger |
|---|---|---|
| Initial load | All entities as nodes (no edges) | Page open |
| Edge reveal | Outgoing edges for a node | Node click / expand |
| Neighbor expansion | Neighbor nodes + their edges | "Expand Neighbors" action |
| Search filter | Client-side node visibility filter | Search input (300ms debounce) |
| Type filter | Client-side node visibility filter | Filter chip toggle |

React Flow manages its own `nodes` and `edges` state. React Query loads the raw entity/relationship data. A `useGraphLayout` hook transforms React Query data into React Flow node/edge format.

### Features

- React Flow canvas: entities as nodes (color by type), relationships as directed labeled edges
- Click node → `EntityInspectorPanel` (Drawer)
- Click edge → `RelationshipInspector` (Tooltip or inline callout)
- "Expand Neighbors" button on each node
- Entity type filter chips (toggle show/hide by type)
- Entity search input (300ms debounce, client-side filter)
- Mini-map
- Zoom in / zoom out / fit-to-view controls
- "Accessible View" toggle — makes `EntityFallbackTable` visible
- `EntityFallbackTable` always present in DOM (`sr-only` by default)
- Empty state when no entities exist
- Entity detail links to related memory entries (via `GET /entities/memory/{memory_id}`)

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/entities/organization/{org_id}` | Initial entity set |
| `GET /api/v1/entities/{entity_id}` | Entity detail for inspector |
| `GET /api/v1/relationships/entity/{id}/outgoing` | Directed edges on expand |
| `GET /api/v1/relationships/entity/{id}/neighbors` | Neighbor nodes on expand |
| `GET /api/v1/relationships/{relationship_id}` | Relationship detail for inspector |
| `GET /api/v1/entities/memory/{memory_id}` | Memory entries linked to entity |

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
| `GraphControls` | `features/graph/GraphControls.tsx` |
| `EntityFallbackTable` | `features/graph/EntityFallbackTable.tsx` |

### Folder Additions

```
features/graph/
  nodes/
  edges/
services/entityService.ts
services/relationshipService.ts
stores/graphStore.ts
types/entity.ts
types/relationship.ts
```

### State Management

- React Query: `['entities', orgId]` staleTime 2min. `['neighbors', entityId]` loaded on demand.
- Zustand `graphStore`: `selectedEntityId`, `expandedNodeIds[]`, `filterType`, `searchTerm`.
- React Flow: internal `useNodesState`, `useEdgesState` for canvas.

### Routing

| Route | Component |
|---|---|
| `/graph` | `KnowledgeGraphPage` |

### Accessibility

- Canvas: `role="application"`, `aria-label="Knowledge graph visualization"`.
- Entity nodes: focusable, `Enter` opens inspector, `Space` triggers neighbor expansion.
- `EntityFallbackTable`: `sr-only` by default; visible via "Accessible View" toggle button.
- Filter chips: `role="group"`, `aria-label="Filter by entity type"`, `aria-pressed` per chip.
- Inspector Drawer: `role="complementary"`, focus managed on open/close.

### Security

- Entity names and descriptions rendered as plain text — no HTML rendering.
- Graph data scoped to `org_id` via Axios interceptor.

### Testing Checklist

- [ ] `GraphCanvas` renders nodes with MSW-mocked entity data
- [ ] Filter chips correctly toggle node visibility
- [ ] `EntityFallbackTable` renders all entities in accessible format
- [ ] Neighbor expansion calls correct endpoint and adds nodes to canvas
- [ ] Empty state when entity list is empty
- [ ] Inspector panel opens on node click

### Performance

- `nodesDraggable: false` by default — significantly reduces React Flow re-renders.
- Edge loading is lazy — never upfront.
- `GraphCanvas` wrapped in `React.memo()`.
- Event handlers wrapped in `useCallback`.
- When entity count exceeds 300, display a "Showing top 300 entities" notice and paginate remaining.

### Validation Checklist

- [ ] Graph renders entity nodes with type-correct colors
- [ ] Directed edges render with relationship type labels
- [ ] Neighbor expansion adds nodes and edges
- [ ] Type filter hides and reveals correct node categories
- [ ] Graph search filters nodes in real time
- [ ] Accessible fallback table is available and navigable
- [ ] Mini-map and zoom controls work
- [ ] Entity inspector links back to memory entries

---

## Milestone 8.4 — AI Chat & Explainability Workspace

### Goal

Build the primary AI interaction surface: a stateful chat backed by the hybrid RAG pipeline, Engineering Copilot (chat, debug, PR review), and a Retrieval Inspector. All AI responses display the full explainability set using `features/explainability/` components.

### Granite Integration Points

| Endpoint | IBM Granite Role |
|---|---|
| `POST /api/v1/chat/ask` | Granite generates the RAG answer; returns citations, confidence, graph_path, retrieval_mode, participating_agents, suggested_actions |
| `POST /api/v1/engineering/chat` | Granite with code-aware system prompt for engineering Q&A |
| `POST /api/v1/engineering/debug` | Granite analyzes stack traces and identifies root cause |
| `POST /api/v1/engineering/review` | Granite reviews PR diff for risk and quality |
| `POST /api/v1/retrieval/explain` | Deterministic scoring only — no Granite; used to inspect raw retrieval |

Every surface that calls a Granite endpoint **must** render all explainability fields. This is a hard requirement for IBM AI Builders Challenge compliance.

### Streaming-Ready Architecture

The backend does not yet support SSE streaming. However, the frontend must be built to enable streaming without a re-architecture when it is added.

**Planning requirements:**
- `chatStore.messages[]` stores messages as objects with `content: string` and `isStreaming: boolean`.
- `ChatMessage` renders content from `message.content` — not from a one-shot API response. This means streaming can feed characters into `content` incrementally.
- `chatStore` includes `abortController: AbortController | null` — used to cancel an in-progress request.
- `ChatInput` includes an "Abort Generation" button shown when `isStreaming: true`.
- `MarkdownRenderer` renders from the current `content` value — safe to be called with partial markdown during streaming.

### Features

- Stateful conversation (messages in `chatStore`, persisted for session)
- `ConversationSidebar` — chat history list (future: multiple conversations)
- `ChatModeSelector` — General RAG / Hybrid GraphRAG / Engineering Copilot tabs
- Chat input: Enter to send, Shift+Enter for newline, character count, Abort button
- Full explainability panel on every response (citations, confidence, mode, graph path, agents, suggested actions) using `features/explainability/`
- Markdown rendering with sanitization
- Code blocks with syntax highlighting and copy button
- `RetrievalExplainPage` — direct retrieval without LLM, per-result score breakdown
- Engineering Copilot: chat, debug, and PR review sub-modes

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
| `MarkdownRenderer` | `features/chat/MarkdownRenderer.tsx` |
| `CodeBlock` | `features/chat/CodeBlock.tsx` |
| `RetrievalExplainPage` | `features/retrieval/RetrievalExplainPage.tsx` |
| `RetrievalResultCard` | `features/retrieval/RetrievalResultCard.tsx` |
| `EngineeringCopilotPage` | `features/engineering/EngineeringCopilotPage.tsx` |
| `DebugPanel` | `features/engineering/DebugPanel.tsx` |
| `PRReviewPanel` | `features/engineering/PRReviewPanel.tsx` |
| *Explainability (all)* | `features/explainability/` — imported, not redefined |

### Folder Additions

```
features/chat/
features/retrieval/
features/engineering/
features/explainability/    ← new module (full list in §5)
services/chatService.ts
services/retrievalService.ts
services/engineeringService.ts
stores/chatStore.ts
types/chat.ts
types/retrieval.ts
types/engineering.ts
```

### State Management

- Zustand `chatStore`: `messages[]`, `activeMode`, `isStreaming`, `abortController`.
- React Query `useMutation`: all chat/engineering/retrieval calls. On success → append to `chatStore.messages`.
- React Hook Form: chat input, debug form (error_message + stack_trace), PR review form.

### Routing

| Route | Component |
|---|---|
| `/chat` | `ChatPage` |
| `/retrieval` | `RetrievalExplainPage` |
| `/engineering` | `EngineeringCopilotPage` |

### Accessibility

- Message list: `role="log"`, `aria-live="polite"`.
- Chat input: `aria-label="Ask a question"`.
- Loading/streaming: `aria-busy="true"` on message list, `aria-live` announcement "Thinking...".
- Code block copy button: `aria-label="Copy code"`, success state announced via `aria-live`.
- Explainability components: see `features/explainability/` accessibility requirements.

### Markdown Rendering Security

`MarkdownRenderer` uses `react-markdown` + `rehype-sanitize`. Allowed tags: `p`, `a`, `code`, `pre`, `strong`, `em`, `ul`, `ol`, `li`, `h1`–`h6`, `blockquote`. Strip all `script`, `style`, `iframe`, and event attributes. This is a security-critical rendering path.

`suggested_actions` are always rendered as `<button>` elements — never as anchor `href` from API data.

### Testing Checklist

- [ ] `ChatPage` sends message, displays response with all explainability fields (MSW)
- [ ] `MarkdownRenderer` renders safe markdown; strips script tags (security test)
- [ ] `CodeBlock` renders code; copy button writes to clipboard
- [ ] `chatStore` appends messages in correct order; maintains conversation
- [ ] `ChatInput` Enter submits; Shift+Enter adds newline
- [ ] Abort button visible when `isStreaming: true`; abort clears streaming state
- [ ] All 5 explainability components render when response metadata is present
- [ ] Empty state when chat history is empty; error state on API failure

### Performance

- Message list uses `react-window` virtualization when messages exceed 50.
- `MarkdownRenderer` is `React.memo` — does not re-render unchanged messages.
- Syntax highlighter imported dynamically.

### Validation Checklist

- [ ] Chat sends question and displays answer with all explainability fields
- [ ] Mode selector changes retrieval strategy correctly
- [ ] Citations render title, type, vector score, graph score
- [ ] Confidence badge renders correct value and color band
- [ ] Graph path renders as ordered breadcrumb
- [ ] Participating agents list renders
- [ ] Suggested actions render as clickable buttons
- [ ] Retrieval explain page shows per-result score breakdown
- [ ] Engineering chat, debug, PR review each produce a formatted response
- [ ] Markdown renders headings, code blocks, and lists correctly

---

## Milestone 8.5 — Multi-Agent Workspace

### Goal

Build the multi-agent UI: agent registry browser, workflow dry-run planner, workflow execution with a timeline view, Repository Agent panel, Debug Agent panel, and conversation history with per-turn agent attribution. All responses use `features/explainability/` components.

### Workflow Timeline UX

The workflow timeline replaces the raw JSON workflow visualization. It represents each agent step as a card in an ordered vertical timeline.

**Timeline steps (matching the backend multi-agent execution chain):**

| Step | Agent | Displays |
|---|---|---|
| 1 | Planner | Question, selected agents, planned steps |
| 2 | Repository Agent | Repository queried, branch, commits retrieved |
| 3 | Debug Agent | Error parsed, incidents identified |
| 4 | Retriever | Memory entries retrieved, vector + graph scores |
| 5 | Granite | Prompt sent, answer generated, tokens used |
| 6 | Explanation Builder | Citations assembled, confidence calculated, graph path built |

Each step card displays: agent name, status (pending/running/complete/error), duration, memory entries used, and any citations produced.

**LangGraph Portability:** The timeline step objects are normalized by `agentsService.ts`. When the backend migrates to LangGraph, only the service layer changes — timeline cards receive the same normalized `WorkflowStep[]` shape.

### Features

- Agent registry grid (one card per agent: name, description, capabilities)
- Workflow panel: question input + agent multi-select + dry-run button
- Dry-run preview: shows `WorkflowPlanPreview` before execution — clearly labelled "Preview — not executed"
- Workflow execution: full response with `WorkflowTimeline` and all explainability fields
- Repository Agent panel: question input, branch selector, answer + commit summary list, file history lookup
- Debug Agent panel: error message + stack trace textarea, incident analysis output
- Conversation history: session-persistent turns, per-turn agent attribution via `ParticipatingAgentsList`
- Execution metrics badge: response time per workflow run

### Backend APIs Required

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/agents/` | List agents |
| `GET /api/v1/agents/{name}` | Agent detail |
| `POST /api/v1/agents/workflow/plan` | Dry-run planner |
| `POST /api/v1/agents/workflow/run` | Execute workflow |
| `POST /api/v1/agents/repository/search` | Repository Agent search |
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
| `WorkflowStepCard` | `features/agents/WorkflowStepCard.tsx` |
| `RepositoryAgentPanel` | `features/agents/RepositoryAgentPanel.tsx` |
| `BranchSelector` | `features/agents/BranchSelector.tsx` |
| `CommitSummaryList` | `features/agents/CommitSummaryList.tsx` |
| `DebugAgentPanel` | `features/agents/DebugAgentPanel.tsx` |
| `ParsedTraceView` | `features/agents/ParsedTraceView.tsx` |
| `ConversationHistoryList` | `features/agents/ConversationHistoryList.tsx` |
| `ConversationTurn` | `features/agents/ConversationTurn.tsx` |
| `ExecutionMetricsBadge` | `features/agents/ExecutionMetricsBadge.tsx` |
| *Explainability (all)* | `features/explainability/` — imported, not redefined |

### Folder Additions

```
features/agents/
services/agentsService.ts
stores/agentStore.ts
types/agents.ts
```

### State Management

- React Query: `useQuery(['agents'])` for registry (staleTime 5min). `useMutation` for workflow/plan, workflow/run, repository search, debug analyze.
- Zustand `agentStore`: `activePanel`, `selectedAgentName`, `workflowHistory[]` (capped at 20 turns).
- React Hook Form: workflow form, repository search form, debug form.

### Routing

| Route | Component / Behavior |
|---|---|
| `/agents` | `AgentsPage` with Tabs for Registry / Workflow / Repository / Debug |
| `/agents/workflow` | Workflow tab active |
| `/agents/repository` | Repository tab active |
| `/agents/debug` | Debug tab active |

### Accessibility

- Dry-run preview: labelled "Preview only — not yet executed" in visible text + `aria-label`.
- Stack trace textarea: `aria-label="Stack trace"`, `spellcheck="false"`.
- `ConversationHistoryList`: `role="log"`, each turn has visible agent name text.
- Suggested actions: `<button>` only — never `<a href>` from API data.
- Workflow timeline: `role="list"`, each step `role="listitem"` with status in visible text.

### Security

- `suggested_actions` always rendered as `<button>` — never anchor `href` from API response data.
- Stack trace content is plain text textarea input — never rendered as HTML.
- Agent names from registry displayed as text — never interpolated into URLs without validation.

### Testing Checklist

- [ ] `AgentRegistryGrid` loads and renders agent cards with MSW mock
- [ ] Dry-run: plan preview renders before execution
- [ ] Workflow execution: `WorkflowTimeline` renders 6 steps with status indicators
- [ ] `RepositoryAgentPanel` search returns answer + commit list
- [ ] `DebugAgentPanel` processes stack trace and shows incident analysis
- [ ] `ConversationHistoryList` renders turns with agent attribution
- [ ] All explainability fields render on workflow response
- [ ] Empty state when no agents registered; error state on API failure

### Performance

- Agent registry prefetched after login.
- `workflowHistory[]` capped at 20 turns in `agentStore`.
- `ParsedTraceView` uses `react-window` for large stack traces.

### Validation Checklist

- [ ] Agent registry displays all registered agents
- [ ] Dry-run returns step plan before execution
- [ ] Workflow run returns full response with all 6 explainability fields
- [ ] Repository search returns answer and commit summaries
- [ ] Branch list loads
- [ ] File history returns commit list
- [ ] Debug Agent returns incident analysis from stack trace
- [ ] Conversation history shows per-turn agent attribution
- [ ] Suggested actions are clickable buttons

---

## Milestone 8.6 — Final Integration & QA

### Goal

Validate the complete application end-to-end. Enforce exit criteria before Sprint 8 is considered complete.

### Features

- Cross-page integration: navigation between all 5 feature areas works without errors
- Analytics charts added to Dashboard (memory count by type, scenario activity)
- Playwright smoke tests: login → dashboard → create memory → chat → graph → agents
- Lighthouse accessibility audit (target: ≥ 90)
- Responsive QA: desktop 1440px, laptop 1280px, tablet 768px
- Error boundary audit: every feature route has a working `<ErrorBoundary>`
- Loading state audit: every async surface shows skeleton/spinner — no blank content
- AI explainability audit: every Granite-powered endpoint surface shows all 5 explainability fields
- Bundle analysis: `vite-bundle-visualizer`, enforce < 500KB initial chunk
- TypeScript strict audit: `tsc --noEmit` with zero errors
- Sprint 8 development journal entry
- README update with frontend setup steps

### Exit Criteria (Sprint 8 is not complete until all pass)

- [ ] All Vitest unit + component tests pass
- [ ] `tsc --noEmit` — zero errors
- [ ] ESLint — zero errors or warnings
- [ ] Lighthouse accessibility score ≥ 90 on all 6 major routes
- [ ] Initial JS bundle < 500KB
- [ ] Playwright smoke tests pass (login → each feature area → logout)
- [ ] Every AI response surface shows: citations, confidence, retrieval mode, graph path, participating agents
- [ ] Every async surface shows loading state and error state
- [ ] Responsive layout validated at 768px, 1280px, 1440px
- [ ] Sprint 8 journal entry written

---

## Shared Component Reuse Map

| Component / Module | Produced in | Reused in |
|---|---|---|
| All `components/ui/` primitives | 8.0 | All milestones |
| `components/feedback/` (LoadingState, EmptyState, ErrorState, Skeleton) | 8.0 | All milestones |
| `lib/api/`, `lib/queryClient.ts` | 8.0 | All service files |
| `authStore`, `WorkspaceLayout`, `AuthGuard` | 8.1 | All authenticated milestones |
| `features/explainability/` (all 9 components) | 8.4 | 8.4, 8.5, future 8.x |
| `MarkdownRenderer`, `CodeBlock` | 8.4 | 8.5 |

---

## Sprint Dependency Graph

```
8.0 Frontend Foundation
  ↓ provides: design system, api client, query client, all primitives
8.1 Authentication + Dashboard
  ↓ provides: authStore, WorkspaceLayout, AuthGuard, navigation config
  ├─── 8.2 Memory Workspace ──────────────────────────────────────────────┐
  └─── 8.3 Knowledge Graph (parallel with 8.2 — no dependency)           │
                                                                           ↓
                                                               8.4 AI Chat + Explainability
                                                                 provides: explainability module
                                                                           ↓
                                                               8.5 Multi-Agent Workspace
                                                                 reuses: explainability module
                                                                           ↓
                                                               8.6 Final Integration + QA
```

---

## Sub-Tasks

### Sub-Task 8.0 — Frontend Foundation
- **Intent:** Bootstrap Vite + React + TypeScript. Configure Tailwind with design tokens. Initialize Shadcn. Assemble provider tree. Build all UI primitives. Set up test infrastructure.
- **Expected Outcomes:** `npm run dev`, `npm run build`, `npm test` all pass. All primitives render. Design tokens visible in DevTools.
- **Status:** [ ] pending

### Sub-Task 8.1 — Authentication & Dashboard
- **Intent:** Login flow, JWT storage, AuthGuard, WorkspaceLayout, navigation config, Dashboard with 6 live widgets.
- **Expected Outcomes:** Full auth cycle works. Dashboard renders live API data. Sidebar driven by `config/navigation.ts`.
- **Status:** [ ] pending

### Sub-Task 8.2 — Memory Workspace
- **Intent:** Memory list, semantic search, scenario navigation, entry drawer with deep-link support, CRUD with cache invalidation.
- **Expected Outcomes:** All memory operations work. Deep-link `/memory/:id` opens drawer. Copy Link works.
- **Status:** [ ] pending

### Sub-Task 8.3 — Knowledge Graph Viewer
- **Intent:** React Flow graph with progressive loading, filter chips, entity/relationship inspectors, accessible fallback table.
- **Expected Outcomes:** Graph renders. Neighbor expansion works. Fallback table accessible. Filters work.
- **Status:** [ ] pending

### Sub-Task 8.4 — AI Chat & Explainability Workspace
- **Intent:** RAG chat, explainability module, retrieval inspector, Engineering Copilot. Streaming-ready architecture.
- **Expected Outcomes:** Chat works. All 5 explainability fields render. Markdown safe. Engineering copilot sub-modes work.
- **Status:** [ ] pending

### Sub-Task 8.5 — Multi-Agent Workspace
- **Intent:** Agent registry, workflow timeline, repository/debug panels, conversation history with attribution.
- **Expected Outcomes:** All 8 agent endpoints integrated. Timeline renders 6 steps. Explainability reused from 8.4.
- **Status:** [ ] pending

### Sub-Task 8.6 — Final Integration & QA
- **Intent:** Full test suite, accessibility audit, performance validation, Playwright smoke tests, release checklist.
- **Expected Outcomes:** All exit criteria in Milestone 8.6 pass. Sprint 8 journal entry complete.
- **Status:** [ ] pending
