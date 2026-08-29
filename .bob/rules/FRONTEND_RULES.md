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

* React
* TypeScript
* Tailwind CSS
* React Router
* React Query
* Zustand
* React Hook Form
* Framer Motion
* React Flow (Knowledge Graph)
* Shadcn UI

## Folder Rules

* app/ contains routing.
* components/ contains reusable UI.
* features/ contains business features.
* hooks/ contains reusable hooks.
* services/ contains API clients.
* stores/ contains Zustand stores.
* lib/ contains utilities.
* types/ contains API types.

Never place API calls directly inside UI components.

## Component Rules

* Keep components under 200 lines when possible.
* Separate UI from logic.
* Use composition over deeply nested components.
* Prefer reusable cards, tables, dialogs, and layouts.

## State Management

* Server state → React Query.
* Client UI state → Zustand.
* Forms → React Hook Form.

## API Rules

* All requests use centralized services.
* JWT handled through auth service.
* Organization ID injected automatically after login.

## API Architecture Rules
* Use one Axios instance only.
* Attach JWT automatically through request interceptor.
* Handle 401 globally.
* Never call fetch() directly inside components.
* Every endpoint has a dedicated service function.
* Every response is typed using shared interfaces.
* React Query owns caching and invalidation.

## AI UI Rules

Always display:

* citations,
* confidence,
* graph path,
* retrieval mode,
* participating agents.

Never hide explainability.

## Performance Rules

* Lazy-load routes.
* Paginate large datasets.
* Debounce search.
* Cache API requests with React Query.

## Accessibility

* Keyboard navigation.
* Focus states.
* ARIA labels.
* Color contrast.
* Screen reader friendly interactions.

## Validation Checklist

Before completing a milestone:

* UI works.
* API integrated.
* Loading/error states exist.
* Empty state exists.
* Responsive validation complete.
* Journal updated.