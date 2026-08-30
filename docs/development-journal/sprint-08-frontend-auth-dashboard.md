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


---

## Entry 04 — Knowledge Graph Workspace (Sprint 8.3)

**Task:** Implement the complete Knowledge Graph Workspace — interactive React Flow canvas, custom nodes and edges, entity inspector drawer, search/filter, neighbor expansion, accessible fallback table, legend, minimap and controls.

**Branch:** `feat/frontend-ai-workspace`
**Date:** 2025-01-09

**Problem:** The `/graph` route did not exist. No entity or relationship services, types, store, or feature components existed. React Flow (`@xyflow/react`) was not installed. The icon registry was missing INCIDENT, FILE, and API_ENDPOINT entity type icons.

**Solution:**

### Package
- Installed `@xyflow/react ^12.11.5`.

### Types
- `types/graph.ts` (new) — `Entity`, `Relationship`, `Neighbor`, `EntityType` (UPPERCASE, mirrors backend), `RelationshipType` (UPPERCASE), `ENTITY_TYPE_COLORS`, `ENTITY_TYPE_LABELS`, `GraphFilters`.
- `types/index.ts` — Added graph type exports with explicit named re-exports to avoid ambiguous `EntityType` collision with `types/api.ts`.

### Services
- `services/entityService.ts` (new) — `listEntities`, `getEntity`, `getEntitiesForMemory`.
- `services/relationshipService.ts` (new) — `getRelationship`, `listOutgoingRelationships`, `listNeighbors`.

### Store
- `stores/graphStore.ts` (new) — Zustand store for selected entity, expanded node IDs (array, not Set for JSON safety), active filters.

### UI Primitives
- `components/ui/Tooltip.tsx` (new) — Radix UI Tooltip wrapper.
- `config/icons.ts` — Added `FileCode2`, `Siren`, `Webhook` icons; added uppercase `EntityType` keys (`PERSON`, `REPOSITORY`, `FILE`, `SERVICE`, `TECHNOLOGY`, `INCIDENT`, `PULL_REQUEST`, `BRANCH`, `API_ENDPOINT`) to `EntityTypeIcons` registry.

### Feature Components
| File | Purpose |
|---|---|
| `EntityNode.tsx` | Custom React Flow node — icon, name, type label, color border |
| `RelationshipEdge.tsx` | Custom React Flow edge — relationship type label, arrow marker |
| `GraphLegend.tsx` | Color legend for all entity types |
| `GraphSearchBar.tsx` | Debounced search (300ms) with `role="search"` |
| `EntityInspectorDrawer.tsx` | Entity detail drawer — description, metadata, expand neighbors |
| `GraphFallbackTable.tsx` | Accessible list/table fallback — keyboard navigable rows |
| `GraphCanvas.tsx` | React Flow canvas — custom nodes/edges, MiniMap, Controls, Background |
| `GraphPage.tsx` | Full page — toolbar, canvas, accessible fallback, entity inspector |

### Key Architectural Decisions
- React Flow data typing: `@xyflow/react` v12 `NodeProps` uses `Record<string, unknown>` for data — cast via `as unknown as EntityNodeData` at component boundary to avoid TypeScript constraint violations.
- Progressive loading: entity list loaded once; neighbor expansion lazy-loads via `listNeighbors` query per expanded entity.
- Filter consistency: client-side filter computed in `GraphPage` and passed to both `GraphCanvas` (visual) and `GraphFallbackTable` (accessible), keeping both surfaces in sync.
- React Flow mock in tests: mocked `@xyflow/react` at module level in test file to avoid jsdom ResizeObserver limitations; all behavior tested through accessible fallback table and inspector drawer.

### Router
- `app/router.tsx` — Added `/graph` lazy route inside `AuthGuard`.

### Tests (MSW + Vitest + RTL)
- `tests/mocks/handlers.ts` — Added entity/relationship fixtures (`mockEntities`, `mockRelationships`, `mockNeighbors`) and handlers for all 6 new endpoints.
- `features/graph/GraphPage.test.tsx` — 16 tests: data state (entities in table, count), loading state, empty state, error + retry, entity row selection → drawer, drawer content/ESC/expand neighbors, search filter, entity type filter, reset graph.

**Validation:**
- `tsc --noEmit` → 0 errors
- `vitest run` → **102/102 tests pass** (16 new tests in Sprint 8.3)
- `vite build` → Clean build — GraphPage 203 kB (65 kB gzip, includes React Flow bundle)

**Security:** No raw HTML rendering anywhere. All entity content is plain text. No backend mutations from graph interactions. Org isolation: `listNeighbors` requires `organization_id` query param — injected from auth store.

**Accessibility:** `role="application"` on canvas. Fallback table uses `role="table"` with keyboard navigation (Enter/Space activates row). Entity inspector drawer: focus trap, `aria-modal`, ESC, `aria-labelledby`. Search: `role="search"` wrapper. Entity type filter: `role="group"` + `aria-label`. Legend: `role="list"`. GraphLegend items: `role="listitem"`.

**Performance:** Lazy-loaded React Flow canvas via `React.lazy`. `useMemo` for nodes/edges arrays. Progressive neighbor loading (one expanded entity at a time). Client-side filter computed in `GraphPage` and shared with both canvas and fallback table.

**Status:** ✅ Complete


---

## Entry 05 — Sprint 8.4 AI Chat Workspace

**Task:** Implement the complete AI Chat Workspace — Granite-powered question answering with full explainability, client-side message history, and all 5 mandatory AI UI Contract fields.

**Branch:** `feat/frontend-ai-workspace`

**Problem:** No chat interface existed. The backend `POST /api/v1/chat/ask` endpoint returns a rich response including a `RetrievalExplanationRead` payload (confidence, citations, graph path, retrieval mode) that must always be shown per the AI UI Contract.

**Solution:**

### Types (`types/chat.ts`)
- `ChatAskRequest`, `ChatAskResponse` — mirror backend `ChatAskRequest`/`ChatAskResponse` Pydantic schemas exactly.
- `CitationRead`, `GraphPathStepRead`, `RetrievalExplanationRead` — mirror `backend/app/schemas/retrieval.py` exactly.
- `ChatMessage` — client-assembled message type (role, content, explanation, suggested_actions, isLoading, error) — never a raw API response stored as-is.
- `ChatSession` — per-session options (scenario_id, use_hybrid).

### Services (`services/chatService.ts`)
- `askChat(request, signal)` — POST `/api/v1/chat/ask` with AbortController signal support.

### Store (`stores/chatStore.ts`)
- `useChatStore` — owns message history assembled client-side (the one legitimate Zustand use for chat per FRONTEND_RULES).
- Actions: `addMessage`, `updateMessage`, `removeMessage`, `clearMessages`, `setScenario`, `setUseHybrid`.

### Explainability Components (`features/explainability/`)
- `CitationPanel` — ranked citation list with score, type, reason, matched entities. Always visible.
- `ConfidenceBadge` — inline score badge with color tiers (high/medium/low) + text label (WCAG 1.4.1 compliance).
- `RetrievalModeTag` — semantic/hybrid/engineering tag with mode-specific styling.
- `GraphPathPanel` — stepwise entity traversal chain. Visible when `graph_path` non-empty.
- `ParticipatingAgentsList` — agent attribution pills. Visible when non-empty.

### Utilities (`utils/markdownRenderer.tsx`)
- `MarkdownRenderer` — `react-markdown` + `rehype-sanitize` + `remark-gfm` with a strict allow-list schema. No `dangerouslySetInnerHTML` anywhere.

### Chat Feature (`features/chat/`)
- `MessageBubble` — user bubble (plain text) + assistant bubble (Markdown answer + all 5 explainability fields + suggested_actions as `<button>` elements only).
- `ChatInput` — React Hook Form textarea, Enter to submit, Shift+Enter for newline, auto-resize, hybrid toggle, scenario selector, character count.
- `ChatPage` — full-screen chat layout with `role="log"` + `aria-live="polite"` message list, React Query `useMutation` for request lifecycle, loading placeholder, error state in bubble, clear conversation.

### Test Infrastructure
- `tests/setup.ts` — Added `window.HTMLElement.prototype.scrollIntoView = function () {}` polyfill for jsdom (canonical pattern).
- `tests/mocks/handlers.ts` — Added `mockExplanation`, `mockChatResponse` fixtures + `POST /api/v1/chat/ask` handler.

### Router
- `app/router.tsx` — Added `/chat` lazy route inside `AuthGuard`.

### Tests (`ChatPage.test.tsx` — 20 tests)
Empty state, send → user bubble, clear input, empty no-submit, loading placeholder, disabled send, assistant answer, explainability panel, ConfidenceBadge score, RetrievalModeTag, CitationPanel count, GraphPathPanel steps, suggested actions as buttons, suggested action click → new message, API error → error bubble, clear conversation, hybrid toggle.

**Validation:**
- `tsc --noEmit` → 0 errors
- `vitest run` → **122/122 tests pass** (20 new in Sprint 8.4)
- `vite build` → Clean build — ChatPage 177 kB (54 kB gzip, includes react-markdown bundle)

**Security:**
- No `dangerouslySetInnerHTML` anywhere. AI responses rendered via `MarkdownRenderer` with `rehype-sanitize` strict schema.
- `suggested_actions` always `<button>` — never `<a href>`.
- JWT injected by Axios interceptor — never in chat request body.
- `organization_id` from auth store — never from URL or form input.

**Accessibility:**
- Message list: `role="log"` + `aria-live="polite"`.
- `ConfidenceBadge`: status not communicated by color alone — includes `<span className="sr-only">High/Medium/Low confidence</span>`.
- Chat input: `<label htmlFor>`, `aria-describedby`, `aria-invalid`, `role="search"` on textarea wrapper.
- Loading state: `aria-busy="true"` on loading container.
- Error: `role="alert"` + `aria-live="assertive"`.

**Status:** ✅ Complete


---

## Entry 06 — Sprint 8.4 Polish: AI Response UI System

**Task:** Refactor AI Chat into a reusable AI Response UI System before Sprint 8.5 commit. Create `AIResponseCard`, `ExplainabilityAccordion`, `StreamingMessage`, `AIWorkspaceHeader`. Upgrade `MarkdownRenderer` with copy-to-clipboard. Add UX improvements: welcome screen, starter prompts, stop-generation button, clear-confirmation dialog, scroll-to-bottom.

**Branch:** `feat/frontend-ai-workspace`

**Problem:** `MessageBubble` contained all explainability rendering inline — not reusable for Engineering Copilot or Multi-Agent Workspace. The original `ChatPage` had a plain clear button with no confirmation, no welcome prompts on empty state, and no streaming-ready architecture.

**Solution:**

### AIResponseCard (`features/chat/AIResponseCard.tsx`)
Single renderer for every Granite-powered assistant response. Layout:
1. **Header** — Granite badge (ibm/granite detection) · `RetrievalModeTag` · `ConfidenceBadge` · timestamp
2. **Answer** — `MarkdownRenderer`
3. **Explainability** — `ExplainabilityAccordion` (collapsed by default, badges always visible in trigger)
4. **Suggested Actions** — `<button>` only, never `<a href>`
5. **ParticipatingAgentsList** — when non-empty

`MessageBubble` now delegates all assistant rendering to `AIResponseCard` — it is a role-switcher only.

### ExplainabilityAccordion (`features/explainability/ExplainabilityAccordion.tsx`)
Radix Accordion-based collapsible "Why this answer?" section. Collapsed by default. Shows `ConfidenceBadge` + `RetrievalModeTag` in trigger (always visible). Expanded content: plain-English summary, stats row (memory count, citations, graph steps), `CitationPanel`, `GraphPathPanel`. Keyboard accessible: Enter/Space to expand, ESC to close.

### StreamingMessage (`features/chat/StreamingMessage.tsx`)
Streaming-ready placeholder component. Empty state: pulsing dots + spinner. Partial content state: partial `MarkdownRenderer` + typing cursor. Respects `prefers-reduced-motion` (Framer Motion `useReducedMotion()`). Screen reader `role="status"` + `aria-live="polite"`.

### AIWorkspaceHeader (`features/chat/AIWorkspaceHeader.tsx`)
Reusable workspace header for AI surfaces. Contains: title, description, icon, IBM Granite attribution badge, organization badge, retrieval mode radio group (semantic/hybrid), clear conversation button. `ChatPage` now uses this instead of an inline header. Designed for reuse in Engineering Copilot and Multi-Agent Workspace (Sprint 8.5).

### MarkdownRenderer upgrade (`utils/markdownRenderer.tsx`)
- Code blocks wrapped in `<div className="relative group">` with language label + copy-to-clipboard `CopyButton`.
- `CopyButton` uses `navigator.clipboard.writeText()` — no `dangerouslySetInnerHTML`. Clipboard access denied → fail silently.
- `aria-label="Copy code to clipboard"` + `data-testid="copy-code-btn"`.
- Inline code rendered with `<code>` styled separately from block code.

### chatStore streaming fields (`stores/chatStore.ts`)
Added: `isStreaming`, `streamingMessageId`, `abortController`. Actions: `startStreaming`, `appendStreamToken`, `stopStreaming`, `abortStreaming`. The `abortController` is stored for Stop Generating to abort from any component.

### ChatPage UX improvements (`features/chat/ChatPage.tsx`)
- **Welcome screen** with 4 starter prompt chips instead of generic `EmptyState`.
- **Stop generating button** — visible while `chatMutation.isPending`, calls `abortStreaming()`.
- **Scroll-to-bottom** — floating button when user scrolls up more than 120px from bottom.
- **Clear confirmation dialog** — Radix Dialog with Cancel / Confirm Destructive.
- **AbortController** passed to `askChat` on every submission. Error on abort shows "Generation stopped."
- `AIWorkspaceHeader` replaces inline header — retrieval mode selector is now a radio group.

**Tests (43 in ChatPage.test.tsx + unit suites):**
- ChatPage: 25 tests (welcome screen, starter prompts, stop button, clear dialog, accordion expand, AIResponseCard, hybrid radio toggle)
- AIResponseCard unit: 8 tests (Granite badge, suggested_actions as buttons, accordion presence)
- ExplainabilityAccordion unit: 5 tests (closed default, expand, collapse, ConfidenceBadge in trigger, defaultOpen)
- MarkdownRenderer unit: 3 tests (copy button, aria-label, inline code)

**Validation:**
- `tsc --noEmit` → 0 errors
- `vitest run` → **145/145 tests pass** (23 new in Entry 06)
- `vite build` → Clean production build — ChatPage 203 kB (62 kB gzip)

**Security:**
- `CopyButton` copies text only via `navigator.clipboard.writeText()` — no HTML execution.
- `AbortController` aborts Axios request cleanly — no dangling network callbacks.
- All AI content continues through `MarkdownRenderer` + `rehype-sanitize`.
- `suggested_actions` remain `<button>` throughout refactor — no regression.

**Accessibility:**
- `ExplainabilityAccordion`: `aria-expanded`, keyboard trigger, Radix manages focus.
- `AIWorkspaceHeader` retrieval selector: `role="radio"` + `aria-checked` + `<fieldset>` + `<legend class="sr-only">`.
- `CopyButton`: `aria-label` updates to "Copied!" on success — state communicated to screen readers.
- `StreamingMessage`: `role="status"` + `aria-live="polite"` announcer for streaming completion.
- Clear dialog: focus trap + ESC close via Radix Dialog.

**Status:** ✅ Complete

