# Frontend Implementation Rules

## Purpose

Enforce permanent architecture constraints during Sprint 8 frontend implementation. These rules apply to every Bob agent session and every human developer working on the TeamMemoryOS frontend. They do not expire.

---

## Rule 1 — API Communication

**Services own all API communication.**

- Every API endpoint has exactly one dedicated function in `services/`.
- Every service function has an explicit TypeScript return type.
- Response shapes mirror backend Pydantic schema field names exactly.
- UI components never call `axios`, `fetch()`, or any HTTP primitive directly.
- `lib/api/client.ts` is the only place an Axios instance is created.

**Violation:** A component imports `axios` directly → reject.
**Violation:** A service function has no return type annotation → reject.

---

## Rule 2 — Server State

**React Query owns all server state.**

- API response data lives in React Query's cache, not in Zustand.
- Use `useQuery` for reads. Use `useMutation` for writes.
- Every mutation that changes a list invalidates the relevant cache key on success.
- Loading and error states come from React Query (`isLoading`, `isError`) — never from local `useState`.
- Cache keys follow the convention: `[resource, scopeId, ...filters]`.

**Violation:** Storing an API response array in a Zustand store → reject.
**Violation:** Using `useState` to track an API loading state → reject.

---

## Rule 3 — Client State

**Zustand owns client-side UI state only.**

Zustand stores may contain:
- JWT token, user object, `organization_id`
- Theme preference, sidebar collapsed state
- Currently selected IDs (not the data behind the ID)
- Chat message history (user-assembled, not raw API responses)
- Graph selection state, agent panel active tab

Zustand stores must never contain:
- API response lists
- Paginated data from the backend
- Form field values
- React Query loading or error states

---

## Rule 4 — Every Page Has All Four States

Every page, panel, or data-displaying component must implement all four states:

1. **Loading** — Skeleton or Spinner from `components/feedback/`.
2. **Error** — `ErrorState` with retry action.
3. **Empty** — `EmptyState` with heading and optional CTA.
4. **Data** — the actual content.

No component ships to review with any of these states missing.

**Check:** Does `MemoryTable` have a skeleton loading state? Does it have an empty state? Does it have an error state? All three must exist.

---

## Rule 5 — AI Explainability (Mandatory, Non-Negotiable)

Every surface that receives a response from a Granite-powered endpoint must render all five explainability fields:

| Field | Component | Visibility |
|---|---|---|
| Citations | `CitationPanel` from `features/explainability/` | Always visible |
| Confidence | `ConfidenceBadge` from `features/explainability/` | Always visible inline |
| Retrieval mode | `RetrievalModeTag` from `features/explainability/` | Always visible inline |
| Graph path | `GraphPathPanel` from `features/explainability/` | Visible when `graph_path` non-empty |
| Participating agents | `ParticipatingAgentsList` from `features/explainability/` | Visible when non-empty |

**None of these may be hidden, collapsed by default, or placed behind a toggle.**

These components are imported from `features/explainability/` — they are never redefined inside another feature.

Granite endpoints:
- `POST /api/v1/chat/ask`
- `POST /api/v1/engineering/chat`
- `POST /api/v1/engineering/debug`
- `POST /api/v1/engineering/review`
- `POST /api/v1/agents/workflow/run`
- `POST /api/v1/agents/repository/search`
- `POST /api/v1/agents/debug/analyze`

---

## Rule 6 — Design System First

Before creating any new UI element, check `components/ui/` first.

Available primitives: Button, Input, Card, Badge, Dialog, Drawer, Table, Tabs, Tooltip, Dropdown, Skeleton, Spinner.
Available feedback: LoadingState, EmptyState, ErrorState.

**If the required component exists:** use it. Do not redefine it.
**If it does not exist:** create it in `components/ui/` — not inside a feature folder.

Never:
- Define a color value inline (use CSS variables).
- Define a spacing value outside Tailwind's scale.
- Define a shadow inline (use `--shadow-*` tokens).
- Create a `Button` inside `features/chat/` when `components/ui/Button.tsx` already exists.

---

## Rule 7 — TDD Before Milestone Completion

Every milestone follows test-first discipline. A milestone is not complete until:

- Every component has a Vitest + RTL test covering: renders with data, loading state, empty state, error state.
- Every form has a test for: valid submit path, invalid submit path (validation errors display).
- Every mutation has a test for: success (cache invalidated), error (error state shown).
- Every dialog/drawer has an accessibility test: focus moves in on open, returns on close, ESC closes.
- MSW is used for all API mocking — no real network calls in tests.

Do not mark a sub-task complete without a passing test suite.

---

## Rule 8 — Folder Ownership

File placement is non-negotiable. Every file goes in the correct folder.

| File type | Correct location |
|---|---|
| React Router route definitions | `app/` |
| Provider initialization | `providers/` |
| Layout wrappers (Sidebar, Topbar, AppShell) | `layouts/` |
| Static config (nav items, constants, theme exports) | `config/` |
| Design system primitives | `components/ui/` |
| Loading/empty/error states | `components/feedback/` |
| Feature pages and feature-local components | `features/<feature>/` |
| AI explainability display components | `features/explainability/` |
| API service functions | `services/` |
| Zustand stores | `stores/` |
| Reusable hooks (cross-feature) | `hooks/` |
| Axios client + interceptors | `lib/api/` |
| Pure utility functions | `utils/` |
| TypeScript interfaces | `types/` |
| CSS and design tokens | `styles/` |

**Violation:** Placing a service call inside a feature component → reject.
**Violation:** Placing a Zustand store inside a feature folder → reject.
**Violation:** Placing explainability components inside `features/chat/` → reject.

---

## Rule 9 — Security Constraints

- Never render user-generated or AI-generated content with `dangerouslySetInnerHTML`.
- `MarkdownRenderer` must use `react-markdown` + `rehype-sanitize` with a strict allow-list schema.
- `suggested_actions` from API responses are always rendered as `<button>` elements — never as `<a href>` tags with API-provided URLs.
- JWT is stored in `localStorage` — this is an accepted trade-off documented in the security section. Token is never logged.
- `org_id` is injected by the Axios interceptor — never read from URL parameters.
- Memory entry and entity content is rendered as plain text — never as HTML.

---

## Rule 10 — Accessibility Baseline

Every component shipped in a milestone must meet WCAG 2.1 AA:

- All interactive elements reachable and operable by keyboard.
- All icon-only controls have `aria-label`.
- Dialogs and drawers: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap, ESC close.
- All form inputs have `<label>` elements linked by `htmlFor` / `id`.
- Error messages linked to inputs via `aria-describedby`.
- Live regions: chat message list uses `role="log"` + `aria-live="polite"`.
- Loading states: `aria-busy="true"` on the container being loaded.
- Status indicators: never communicated by color alone — always include text.
- All Framer Motion animations check `useReducedMotion()`.

---

## Rule 11 — Performance Baseline

- All feature routes use `React.lazy()` + `<Suspense>`.
- No barrel imports from Shadcn, Lucide, or any icon library.
- Search inputs debounced at 300ms (`DEBOUNCE_MS` from `config/constants.ts`).
- Paginated lists use `keepPreviousData: true`.
- Lists exceeding 100 items use `react-window` virtualization.
- React Flow graphs use lazy edge loading and `nodesDraggable: false` by default.

---

## Validation Checklist (Per Milestone)

Before marking any milestone sub-task complete:

- [ ] UI renders correctly with real API data
- [ ] Loading state (skeleton/spinner) present
- [ ] Empty state present
- [ ] Error state present with retry
- [ ] All forms have validation (valid + invalid paths tested)
- [ ] All AI response surfaces show all 5 explainability fields
- [ ] Keyboard navigation works for all interactive elements
- [ ] `tsc --noEmit` passes with zero errors
- [ ] `npm test` passes
- [ ] Responsive at 768px tablet viewport
- [ ] No console errors or warnings
- [ ] Development journal entry appended
