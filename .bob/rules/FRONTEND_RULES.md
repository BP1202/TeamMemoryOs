# TeamMemoryOS Frontend Rules

## Purpose

Build TeamMemoryOS as a premium AI Operating System frontend using the backend APIs built in Sprints 1–7.

## Frontend Principles

* Desktop-first experience.
* Responsive layouts for tablet/mobile.
* Accessibility-first components.
* API-first architecture.
* Reusable UI system.
* No duplicated backend business logic.

## Technology Stack

* React 18
* TypeScript (strict mode)
* Vite
* Tailwind CSS
* React Router v6
* React Query v5
* Zustand v4
* React Hook Form v7
* Framer Motion
* React Flow (Knowledge Graph)
* Shadcn UI

## Folder Ownership

Every folder has a single, bounded responsibility. Violations are rejected at review.

| Folder | Owns | Never contains |
|---|---|---|
| `app/` | Route definitions + lazy imports | Business logic, API calls, state |
| `providers/` | Provider initialization + composition order | Feature logic, UI rendering |
| `layouts/` | Structural page wrappers | Feature data, API calls |
| `config/` | Static configuration objects | Runtime logic, React components |
| `components/ui/` | Design system primitives | API calls, business logic, store reads |
| `components/feedback/` | Loading, empty, error, skeleton states | Feature-specific content |
| `features/` | Feature pages + feature-local components | Direct `fetch()` / `axios` |
| `features/explainability/` | AI explainability display components | Chat logic, agent orchestration |
| `services/` | One typed function per API endpoint | React components, hooks, stores |
| `stores/` | Client UI state + session state | Server response lists, loading flags |
| `hooks/` | Reusable hook logic shared across features | Component JSX |
| `lib/api/` | Axios client + interceptor modules | Feature logic, store reads |
| `utils/` | Pure helper functions | React, side effects |
| `types/` | TypeScript interface definitions | Runtime logic, default values |

## Component Ownership

* Keep components under 200 lines.
* Separate UI from logic using hooks.
* Use composition over deeply nested components.
* `components/ui/` components never read from any store or service.
* Feature components call services through React Query hooks — never directly.
* `features/explainability/` components receive all data as props — they are pure display components.

## State Ownership

* **Server state** → React Query. Never in Zustand.
* **Client UI state** → Zustand. Never server response data.
* **Form state** → React Hook Form. Never in useState or Zustand.

### What belongs in Zustand

* JWT token, user object, organization_id (persisted to localStorage)
* Theme, sidebar collapsed state
* Currently selected IDs (not the data behind the ID)
* Chat message history (assembled client-side)
* Graph selection state, agent active panel tab

### What never belongs in Zustand

* API response lists
* Paginated data
* Form field values
* React Query loading or error states

## Explainability Ownership

Every surface backed by a Granite-powered endpoint must always render all five fields:

* `CitationPanel` — always visible
* `ConfidenceBadge` — always visible inline
* `RetrievalModeTag` — always visible inline
* `GraphPathPanel` — visible when `graph_path` non-empty
* `ParticipatingAgentsList` — visible when non-empty

All explainability components live in `features/explainability/` and are never redefined elsewhere.
Never hide explainability behind a toggle or collapse by default.

## API Architecture Rules

* One Axios instance only (`lib/api/client.ts`).
* JWT injected automatically via `lib/api/auth.ts` request interceptor.
* `X-Organization-ID` injected automatically via `lib/api/organization.ts` request interceptor.
* Global 401 handling in `lib/api/errors.ts` — clears auth store and redirects to `/login`.
* All errors normalized to typed `ApiError` before reaching feature code.
* Never call `fetch()` directly inside components or features.
* Every endpoint has a dedicated service function.
* Every response typed using shared interfaces in `types/`.
* React Query owns caching and invalidation.
* `AbortController` signals passed to all list and search queries via React Query `signal`.

## Accessibility Ownership

* Keyboard navigation — all interactive elements reachable and operable.
* All icon-only controls have `aria-label`.
* Dialogs/drawers: focus trap, ESC close, `aria-modal`, `aria-labelledby`.
* Form inputs: `<label>` linked by `htmlFor`, errors linked via `aria-describedby`.
* Live regions: chat uses `role="log"` + `aria-live="polite"`.
* Loading: `aria-busy="true"` on the loading container.
* Status: never by color alone — always include text.
* Framer Motion: always check `useReducedMotion()`.
* Color contrast: WCAG AA minimum (4.5:1 text, 3:1 UI elements).

## Performance Ownership

* Lazy-load routes — all feature routes use `React.lazy()` + `<Suspense>`.
* No barrel imports from Shadcn, Lucide, or icon libraries.
* Paginate large datasets — default page size 20.
* `keepPreviousData: true` on all paginated list queries.
* Debounce search inputs at 300ms.
* Cache API requests with React Query (staleTime per resource type).
* React Flow: lazy edge loading, `nodesDraggable: false` by default.
* Lists > 100 items use `react-window` virtualization.

## Security Ownership

* JWT stored in `localStorage` — documented risk, accepted for SPA.
* Token never logged to console or included in error messages.
* No `dangerouslySetInnerHTML` anywhere in the application.
* `MarkdownRenderer` uses `react-markdown` + `rehype-sanitize` with strict allow-list schema.
* `suggested_actions` always rendered as `<button>` — never as `<a href>` from API data.
* `org_id` injected by Axios interceptor — never read from URL parameters.
* User-generated and AI-generated content rendered as plain text — never as HTML.

## Testing Ownership

* Every feature follows TDD: tests written before milestone is marked complete.
* Every component requires: data state test, loading state test, empty state test, error state test.
* Every form requires: valid submit path test, invalid submit path test.
* Every mutation requires: success path test (cache invalidated), error path test.
* Every dialog/drawer requires: focus management test, ESC close test.
* MSW for all API mocking — no real network calls in tests.
* Accessibility snapshot for every modal and dialog.
* Stack: Vitest + React Testing Library + MSW. Playwright for E2E in Milestone 8.6.

## Validation Checklist

Before completing any milestone:

* UI works with real API data.
* API integrated through services layer.
* Loading state (skeleton/spinner) present.
* Error state present with retry action.
* Empty state present.
* All AI responses show all 5 explainability fields.
* All forms have validation tested.
* Keyboard navigation verified.
* `tsc --noEmit` passes with zero errors.
* `npm test` passes.
* Responsive at 768px viewport.
* No console errors or warnings.
* Development journal entry appended.
