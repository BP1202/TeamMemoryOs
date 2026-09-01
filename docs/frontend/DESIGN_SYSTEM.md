# TeamMemoryOS Design System

> **Source of truth:** `frontend/config/design-tokens.ts`
> **CSS variables:** `frontend/styles/tokens.css`
> **Tailwind config:** `frontend/tailwind.config.ts`

This document describes the design token architecture for the TeamMemoryOS frontend. Every visual value in the application — colors, spacing, typography, shadows, radius, z-index, animation — originates from a single registry. No component hardcodes these values.

---

## Architecture

```
frontend/config/design-tokens.ts   ← Canonical token registry (TypeScript)
        ↓                   ↓
frontend/styles/tokens.css    frontend/tailwind.config.ts
(CSS custom properties)       (Tailwind theme extension)
        ↓                   ↓
React components reference    Tailwind utility classes
  var(--token-name)           reference token values
```

### Three Representations, One Source

| File | Format | Consumer |
|---|---|---|
| `config/design-tokens.ts` | TypeScript `as const` objects | Framer Motion, Jest, canvas rendering |
| `styles/tokens.css` | CSS custom properties (`:root`) | CSS transitions, Tailwind `var()` references |
| `tailwind.config.ts` | Tailwind theme extension | Utility classes in JSX |

All three files are kept in sync. When a token value changes, change it in `design-tokens.ts` first. The Tailwind config imports from `design-tokens.ts` directly. The CSS file is the only file updated manually alongside `design-tokens.ts`.

---

## Token Ownership Rules

- **Never hardcode a hex value in a component.** Use Tailwind classes or CSS variables.
- **Never add a new color directly to Tailwind config.** Add it to `design-tokens.ts` first.
- **Tokens are immutable constants.** Modify them only when updating the system intentionally.
- **CSS variable names mirror token paths exactly.** `colors.brand.default` → `--color-brand-default`.
- **Framer Motion durations reference `animation.duration.*` from `design-tokens.ts`**, not hardcoded millisecond values.

---

## Color Palette

### Surface Backgrounds

Use in order from outermost canvas to innermost elevated surface.

| Token | CSS Variable | Value | Usage |
|---|---|---|---|
| `colors.surface.base` | `--color-surface-base` | `#0a0a0f` | Root page canvas |
| `colors.surface.default` | `--color-surface-default` | `#111118` | Cards, panels, sidebars |
| `colors.surface.elevated` | `--color-surface-elevated` | `#1a1a24` | Dropdowns, dialogs, popovers |
| `colors.surface.subtle` | `--color-surface-subtle` | `#22222f` | Hover highlights, row backgrounds |
| `colors.surface.overlay` | `--color-surface-overlay` | `rgba(10,10,15,0.8)` | Modal backdrop |

### Brand — Indigo

| Token | CSS Variable | Value | Usage |
|---|---|---|---|
| `colors.brand.default` | `--color-brand-default` | `#6366f1` | Primary buttons, active indicators |
| `colors.brand.hover` | `--color-brand-hover` | `#818cf8` | Button hover, link hover |
| `colors.brand.muted` | `--color-brand-muted` | `#312e81` | Muted brand backgrounds |
| `colors.brand.subtle` | `--color-brand-subtle` | `#1e1b4b` | Very subtle brand tint |
| `colors.brand.ring` | `--color-brand-ring` | `rgba(99,102,241,0.5)` | Focus rings |

### Semantic Status

| Group | Default | Muted | Subtle |
|---|---|---|---|
| Success | `#22c55e` | `#14532d` | `#052e16` |
| Warning | `#f59e0b` | `#78350f` | `#451a03` |
| Danger | `#ef4444` | `#7f1d1d` | `#450a0a` |
| Info | `#38bdf8` | `#0c4a6e` | `#082f49` |

### Text Hierarchy

| Token | Value | Usage |
|---|---|---|
| `colors.text.primary` | `#f1f5f9` | Main readable text |
| `colors.text.secondary` | `#94a3b8` | Supporting labels, meta info |
| `colors.text.muted` | `#475569` | Placeholders, disabled |
| `colors.text.inverse` | `#0a0a0f` | Text on light backgrounds |
| `colors.text.link` | `#818cf8` | Inline links |
| `colors.text.code` | `#c084fc` | Inline code spans |

### Confidence Banding (AI Explainability)

These tokens are used **exclusively** by `features/explainability/` components. They map a 0.0–1.0 confidence score from IBM Granite to a visual tier.

| Score Range | Tier | Color | CSS Variable |
|---|---|---|---|
| > 0.75 | High | `#22c55e` (green) | `--color-confidence-high` |
| 0.5 – 0.75 | Medium | `#f59e0b` (amber) | `--color-confidence-medium` |
| < 0.5 | Low | `#ef4444` (red) | `--color-confidence-low` |

Each tier also has a muted background variant (`-muted`) for badge backgrounds.

**Tailwind classes:**
```html
<span class="text-confidence-high bg-confidence-high-muted">High</span>
<span class="text-confidence-medium bg-confidence-medium-muted">Medium</span>
<span class="text-confidence-low bg-confidence-low-muted">Low</span>
```

### Entity Type Colors (Knowledge Graph)

Used by `GraphCanvas` node coloring and the `colorFromType` utility in `utils/colorFromType.ts`.

| Entity Type | Color | Tailwind Class |
|---|---|---|
| person | `#818cf8` | `bg-entity-person` |
| technology | `#38bdf8` | `bg-entity-technology` |
| project | `#34d399` | `bg-entity-project` |
| decision | `#f59e0b` | `bg-entity-decision` |
| concept | `#c084fc` | `bg-entity-concept` |
| organization | `#f97316` | `bg-entity-organization` |
| (default) | `#94a3b8` | `bg-entity-default` |

### Memory Type Colors

Used by `MemoryTypeBadge` component.

| Type | Color | Tailwind Class |
|---|---|---|
| DECISION | `#f59e0b` | `text-memory-decision` |
| CODE | `#38bdf8` | `text-memory-code` |
| DISCUSSION | `#818cf8` | `text-memory-discussion` |
| DOCUMENTATION | `#34d399` | `text-memory-documentation` |
| INCIDENT | `#ef4444` | `text-memory-incident` |

---

## Typography

### Font Families

```
--font-sans: 'Inter', system-ui, sans-serif
--font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace
```

Tailwind: `font-sans`, `font-mono`

### Type Scale

| Name | Size | Line Height | Usage |
|---|---|---|---|
| `text-xs` | 12px | 16px | Labels, badges, captions |
| `text-sm` | 14px | 20px | Body secondary, table cells |
| `text-base` | 16px | 24px | Body primary |
| `text-lg` | 18px | 28px | Subheadings |
| `text-xl` | 20px | 28px | Section headings |
| `text-2xl` | 24px | 32px | Page headings |
| `text-3xl` | 30px | 36px | Hero headings |
| `text-4xl` | 36px | 40px | Display |

### Semantic Text Styles

These are named roles that combine size + weight + tracking. Documented here as implementation guidance — they are not Tailwind classes, but composed Tailwind class sets.

| Role | Size | Weight | Tracking |
|---|---|---|---|
| display | 4xl | bold | tight |
| heading | 3xl | bold | tight |
| title | 2xl | semibold | normal |
| subtitle | xl | medium | normal |
| body | base | normal | normal |
| bodySmall | sm | normal | normal |
| caption | xs | normal | wide |
| code | sm | normal | normal |
| label | xs | medium | wider |

---

## Spacing

4px base unit. Follows Tailwind's default scale (1 unit = 4px). Semantic aliases are added for recurring layout values.

| Semantic Token | Value | Usage |
|---|---|---|
| `spacing.inputX` | 12px | Input field horizontal padding |
| `spacing.inputY` | 8px | Input field vertical padding |
| `spacing.cardPadding` | 24px | Standard card internal padding |
| `spacing.pagePadding` | 32px | Outer page horizontal padding |
| `spacing.sectionGap` | 40px | Gap between major page sections |
| `spacing.sidebarW` | 240px | Sidebar expanded width |
| `spacing.sidebarCollapsedW` | 64px | Sidebar collapsed width |
| `spacing.topbarH` | 56px | Topbar height |

Tailwind classes for semantic values: `w-sidebar`, `w-sidebar-collapsed`, `h-topbar`, `p-card`, `px-page`, `gap-section`.

---

## Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius.xs` | 2px | Very subtle rounding (inline code) |
| `radius.sm` | 4px | Small tags, badges |
| `radius.md` | 8px | Buttons, inputs, most cards |
| `radius.lg` | 12px | Larger cards |
| `radius.xl` | 16px | Panels, drawers |
| `radius.2xl` | 24px | Large featured components |
| `radius.full` | 9999px | Pills, circular avatars |

Tailwind: `rounded-xs`, `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-full`

---

## Shadows / Elevation

All shadows are tuned for dark surfaces.

**Rule:** Use the lowest elevation that creates sufficient visual separation.

| Token | CSS Variable | Usage |
|---|---|---|
| `shadows.sm` | `--shadow-sm` | Subtle lifted elements |
| `shadows.md` | `--shadow-md` | Cards (default) |
| `shadows.lg` | `--shadow-lg` | Drawers, side panels |
| `shadows.xl` | `--shadow-xl` | Modals, dialogs |
| `shadows.glow` | `--shadow-glow` | Brand focus/active glow |
| `shadows.danger` | `--shadow-danger` | Destructive focus ring |
| `shadows.card` | `--shadow-card` | Standard card shadow |
| `shadows.dialog` | `--shadow-dialog` | Dialog/modal backdrop shadow |
| `shadows.drawer` | `--shadow-drawer` | Side drawer shadow |

Tailwind: `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-glow`, `shadow-danger`, `shadow-card`, `shadow-dialog`, `shadow-drawer`

---

## Z-Index Layers

**Rule:** Never use an arbitrary z-index. Always use a named layer.

| Layer | Value | Usage |
|---|---|---|
| `zIndex.base` | 0 | Default document flow |
| `zIndex.raised` | 1 | Table row hover, slightly elevated |
| `zIndex.sidebar` | 20 | Fixed sidebar |
| `zIndex.topbar` | 30 | Fixed topbar (above sidebar) |
| `zIndex.drawer` | 40 | Slide-in drawer |
| `zIndex.modal` | 50 | Dialogs and modals |
| `zIndex.popover` | 60 | Dropdowns, popovers (above modals) |
| `zIndex.tooltip` | 70 | Tooltips |
| `zIndex.toast` | 80 | Toast notifications (always topmost) |

Tailwind: `z-sidebar`, `z-topbar`, `z-drawer`, `z-modal`, `z-popover`, `z-tooltip`, `z-toast`

---

## Animation

### Duration Tokens

| Token | Value | Usage |
|---|---|---|
| `animation.duration.fast` | 150ms | Hover states, focus rings |
| `animation.duration.medium` | 200ms | Panel entrances, dialogs |
| `animation.duration.slow` | 300ms | Page transitions |
| `animation.duration.verySlow` | 500ms | Complex layout shifts (sparingly) |

Tailwind: `duration-fast`, `duration-medium`, `duration-slow`, `duration-very-slow`

### Easing Tokens

| Token | Curve | Usage |
|---|---|---|
| `animation.easing.easeOut` | `cubic-bezier(0,0,0.2,1)` | Most entering elements |
| `animation.easing.easeIn` | `cubic-bezier(0.4,0,1,1)` | Exiting elements |
| `animation.easing.easeInOut` | `cubic-bezier(0.4,0,0.2,1)` | Toggle transitions |
| `animation.easing.spring` | `cubic-bezier(0.34,1.56,0.64,1)` | Interactive feedback |

Tailwind: `ease-out`, `ease-in`, `ease-in-out`, `ease-spring`

### Framer Motion Variant Patterns

Import from `design-tokens.ts` and spread into `motion` component `variants` prop:

```typescript
import { animation } from '@/config/design-tokens';

// Page entrance
<motion.div
  variants={animation.variants.fadeUp}
  initial="hidden"
  animate="visible"
  exit="exit"
/>

// Drawer
<motion.aside
  variants={animation.variants.slideRight}
  initial="hidden"
  animate="visible"
  exit="exit"
/>

// Staggered list
<motion.ul variants={animation.variants.staggerContainer} initial="hidden" animate="visible">
  {items.map(item => (
    <motion.li key={item.id} variants={animation.variants.listItem}>...</motion.li>
  ))}
</motion.ul>
```

### Reduced Motion

All Framer Motion components must check `useReducedMotion()`:

```typescript
import { useReducedMotion } from 'framer-motion';

const prefersReduced = useReducedMotion();
const duration = prefersReduced ? 0 : animation.duration.medium;
```

CSS transitions are automatically disabled via the `@media (prefers-reduced-motion: reduce)` block in `styles/tokens.css`.

---

## Breakpoints

Desktop-first layout. Design for 1440px, then adapt downward.

| Name | Value | Target |
|---|---|---|
| `xs` | 480px | Large mobile |
| `sm` | 640px | Small tablet |
| `md` | 768px | Tablet — minimum supported viewport |
| `lg` | 1024px | Laptop |
| `xl` | 1280px | Desktop |
| `2xl` | 1536px | Wide desktop |

---

## Component Tokens

Component tokens map each UI component variant to its resolved primitive token values. They sit between the raw design tokens (colors, spacing, radius) and the actual component implementation. This intermediate layer means changing a component's visual style requires only a single update — to its component token block — rather than hunting for hardcoded values in JSX.

### Layer Hierarchy

```
colors.brand.default          ← Primitive token (design-tokens.ts)
  ↓
--color-brand-default         ← Primitive CSS variable (tokens.css)
  ↓
--btn-primary-bg              ← Component token CSS variable (tokens.css)
  ↓
componentTokens.button.primary.bg  ← TypeScript component token (design-tokens.ts)
  ↓
className="bg-[var(--btn-primary-bg)]"   ← Component usage
```

### Button

| Variant | bg | bgHover | text | border | ring | shadow |
|---|---|---|---|---|---|---|
| `primary` | `--btn-primary-bg` | `--btn-primary-bg-hover` | white | transparent | brand-ring | glow |
| `secondary` | `--btn-secondary-bg` | `--btn-secondary-bg-hover` | text-primary | border-default | brand-ring | none |
| `ghost` | transparent | `--btn-ghost-bg-hover` | text-secondary | transparent | brand-ring | none |
| `destructive` | `--btn-destructive-bg` | `--btn-destructive-bg-hover` | white | transparent | danger-ring | danger |

All button variants share:
- `border-radius: var(--btn-border-radius)` → `--radius-md`
- `font-weight: var(--btn-font-weight)` → `--font-medium`
- `transition: background var(--btn-transition-duration) var(--btn-transition-easing)`

Disabled state on every variant: `bg-surface-elevated`, `text-text-muted`, `cursor-not-allowed`.

### Card

| Variant | bg | border | shadow | Use for |
|---|---|---|---|---|
| `default` | `--card-default-bg` | `--card-default-border` | `--shadow-card` | Most content panels |
| `elevated` | `--card-elevated-bg` | `--card-elevated-border` | `--shadow-md` | Dialogs, callout cards |
| `outline` | transparent | `--card-outline-border` | none | Secondary cards, selectable items |

`outline` adds `--card-outline-bg-hover` and `--card-outline-border-hover` on hover for interactive card lists.

### Input

| State | bg | border | ring | shadow |
|---|---|---|---|---|
| `default` | `--input-bg` | `--input-border` | — | none |
| `focus` | `--input-bg` | `--input-focus-border` | `--input-focus-ring` | glow |
| `error` | `--input-bg` | `--input-error-border` | `--input-error-ring` | danger |
| `disabled` | `--input-disabled-bg` | `--input-disabled-border` | — | none |

Error state also sets label and hint text to `--input-error-label` / `--input-error-label` (danger color).

### Badge

| Variant | bg CSS var | text CSS var | Use for |
|---|---|---|---|
| `success` | `--badge-success-bg` | `--badge-success-text` | Health OK, test pass, high confidence |
| `warning` | `--badge-warning-bg` | `--badge-warning-text` | Degraded, needs review |
| `danger` | `--badge-danger-bg` | `--badge-danger-text` | Error, failed, critical |
| `info` | `--badge-info-bg` | `--badge-info-text` | Neutral labels, metadata |
| `default` | `--badge-default-bg` | `--badge-default-text` | Uncategorized tags |

All badges share: `border-radius: var(--badge-border-radius)` (→ `--radius-full`), `font-size: var(--badge-font-size)` (→ `--text-xs`), `font-weight: var(--badge-font-weight)` (→ `--font-medium`).

### AI Explainability Component Tokens

> These tokens are **exclusively** for `features/explainability/` components. Never use `--ai-*` variables in general UI primitives.

#### Confidence Badge

| Tier | Score range | bg var | text var | icon var |
|---|---|---|---|---|
| `confidenceHigh` | > 0.75 | `--ai-confidence-high-bg` | `--ai-confidence-high-text` | `--ai-confidence-high-icon` |
| `confidenceMedium` | 0.5–0.75 | `--ai-confidence-medium-bg` | `--ai-confidence-medium-text` | `--ai-confidence-medium-icon` |
| `confidenceLow` | < 0.5 | `--ai-confidence-low-bg` | `--ai-confidence-low-text` | `--ai-confidence-low-icon` |

All confidence badges share `border-radius: var(--ai-confidence-border-radius)` (→ pill).

The `ConfidenceBadge` component selects the correct tier by comparing the numeric score from the Granite API response:

```typescript
import { componentTokens } from '@/config/design-tokens';

function getConfidenceTier(score: number) {
  if (score > 0.75) return componentTokens.ai.confidenceHigh;
  if (score >= 0.5) return componentTokens.ai.confidenceMedium;
  return componentTokens.ai.confidenceLow;
}
```

#### Retrieval Mode Tag

| Mode | bg var | text var | When used |
|---|---|---|---|
| `retrievalSemantic` | `--ai-retrieval-semantic-bg` | `--ai-retrieval-semantic-text` | Vector similarity only |
| `retrievalHybrid` | `--ai-retrieval-hybrid-bg` | `--ai-retrieval-hybrid-text` | Vector + Knowledge Graph |
| `retrievalEngineering` | `--ai-retrieval-engineering-bg` | `--ai-retrieval-engineering-text` | Engineering Copilot mode |

#### Citation Card

| Property | CSS var |
|---|---|
| Background | `--ai-citation-bg` |
| Default border | `--ai-citation-border` |
| Left accent border | `--ai-citation-border-accent` (3px brand-colored left strip) |
| Text | `--ai-citation-text` |
| Meta text (score, rank) | `--ai-citation-meta-text` |

#### Graph Path Breadcrumb

| Property | CSS var |
|---|---|
| Item text | `--ai-graph-path-text` |
| Active item text | `--ai-graph-path-text-active` |
| Separator | `--ai-graph-path-separator` |
| Active item background | `--ai-graph-path-bg-active` |

### How to Add a New Component Variant

1. Add the variant object to the relevant group in `componentTokens` inside `frontend/config/design-tokens.ts`.
2. Add the corresponding `--component-*` CSS variables to the Component Tokens block in `frontend/styles/tokens.css`. Reference primitive token vars — never raw hex values.
3. Document the variant in this section.
4. Do not modify `tailwind.config.ts` for component tokens — components use `var()` references directly.

---

## How to Add a New Token

1. Add the value to the appropriate group in `frontend/config/design-tokens.ts`.
2. Add the corresponding CSS variable to `frontend/styles/tokens.css`.
3. The Tailwind config auto-imports from `design-tokens.ts` — no change needed for Tailwind unless a new group is introduced.
4. Document the token in this file under the appropriate section.
5. Never skip step 2 — CSS variables must always mirror TypeScript tokens.

---

## How to Use Tokens in Components

### Tailwind classes (preferred)

```tsx
// Background
<div className="bg-surface-default border border-border">

// Text
<p className="text-text-primary">Main content</p>
<span className="text-text-muted text-sm">Supporting label</span>

// Brand button
<button className="bg-brand hover:bg-brand-hover text-white rounded-md shadow-glow">

// Confidence badge (AI explainability)
<span className="text-confidence-high bg-confidence-high-muted rounded-full px-2 py-0.5 text-xs font-medium">
  High
</span>
```

### CSS variables (for custom CSS or inline animation styles)

```css
.custom-panel {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  transition: box-shadow var(--duration-medium) var(--ease-out);
}
```

### TypeScript tokens (for Framer Motion or canvas)

```typescript
import tokens from '@/config/design-tokens';

// Framer Motion
const transition = {
  duration: tokens.animation.duration.medium / 1000, // Framer uses seconds
  ease: tokens.animation.framerEasing.easeOut,
};

// Canvas / React Flow node color
const nodeColor = tokens.colors.entityType[entityType] ?? tokens.colors.entityType.default;
```

---

## Icon Registry

**Source of truth:** [`frontend/config/icons.ts`](../frontend/config/icons.ts)

All Lucide React icons are imported and re-exported through this central registry. Feature components and UI primitives never import from `lucide-react` directly.

### Why a Central Registry

- A single import change updates every usage site when an icon is replaced.
- Icon groups align 1:1 with domain concepts — `MemoryTypeIcons.DECISION` communicates intent better than a bare `Lightbulb` import.
- Enforces consistent sizing via `iconSize` constants.
- Prevents duplicate icon imports across the bundle.

### Importing Icons

```typescript
// Named group import (preferred)
import { NavIcons, StatusIcons, AIIcons, iconSize } from '@/config/icons';

<NavIcons.Memory className={iconSize.nav} />
<StatusIcons.success className={iconSize.button} />
<AIIcons.confidence className={iconSize.inline} />
```

### Icon Size Constants

| Key | Tailwind class | Size | Usage |
|---|---|---|---|
| `inline` | `h-4 w-4` | 16px | Inline text, table cells, dense lists |
| `button` | `h-5 w-5` | 20px | Button icons, action triggers |
| `nav` | `h-5 w-5` | 20px | Sidebar navigation items |
| `heading` | `h-6 w-6` | 24px | Page headings, empty state icons |
| `feature` | `h-8 w-8` | 32px | Large decorative icons |

### Navigation Icons

| Key | Icon | Route |
|---|---|---|
| `Dashboard` | `LayoutDashboard` | `/` |
| `Memory` | `Database` | `/memory` |
| `Graph` | `Network` | `/graph` |
| `Chat` | `MessageSquare` | `/chat` |
| `Agents` | `Bot` | `/agents` |
| `Settings` | `Settings` | `/settings` |

Keys match the route/feature name used in `config/navigation.ts`.

### Memory Type Icons

Keys match `MemoryEntry.memory_type` enum values from the backend exactly.

| Key | Icon | When used |
|---|---|---|
| `DECISION` | `Lightbulb` | Engineering or product decision |
| `INCIDENT` | `AlertTriangle` | Production incident, post-mortem |
| `DOCUMENTATION` | `BookOpen` | ADR, runbook, reference docs |
| `CODE` | `Code2` | Code snippet, implementation note |
| `DISCUSSION` | `MessagesSquare` | Meeting notes, Slack thread |

### Entity Type Icons

Keys match `Entity.entity_type` values from the backend exactly.

| Key | Icon | Entity |
|---|---|---|
| `person` | `User` | Human contributor or stakeholder |
| `technology` | `Cpu` | Framework, language, or tool |
| `repository` | `GitBranch` | Git repository |
| `service` | `Server` | Deployed service or microservice |
| `api` | `Plug` | External API or integration |
| `pull_request` | `GitPullRequest` | Pull request |
| `branch` | `GitBranchPlus` | Git branch |

### Status Icons

Always paired with a text label — never used as the sole indicator of status.

| Key | Icon | Meaning |
|---|---|---|
| `success` | `CheckCircle2` | Healthy, passed, complete |
| `warning` | `AlertCircle` | Degraded, needs attention |
| `error` | `XCircle` | Failed, unavailable |
| `info` | `Info` | Neutral informational |
| `pending` | `Clock` | In progress, queued |

### AI Explainability Icons

Used exclusively by `features/explainability/` components. Each icon is paired with the corresponding explainability field from the Granite API response.

| Key | Icon | Paired with |
|---|---|---|
| `citation` | `Quote` | `CitationPanel` — memory sources |
| `confidence` | `BarChart2` | `ConfidenceBadge` — numeric score |
| `graphPath` | `Waypoints` | `GraphPathPanel` — entity traversal chain |
| `hybridRetrieval` | `Merge` | `RetrievalModeTag` — hybrid mode |
| `granite` | `Sparkles` | IBM Granite model attribution |

### How to Add a New Icon

1. Find the icon name at [lucide.dev](https://lucide.dev).
2. Import it at the top of `frontend/config/icons.ts`.
3. Add it to the appropriate group constant, or to `UtilityIcons` if it is general-purpose.
4. Export any new type key if the group gains a new entry (e.g. `AIIconKey`).
5. Document the addition in this section.

Never add a Lucide import directly inside a component file.

---

## Files Reference

| File | Purpose |
|---|---|
| `frontend/config/design-tokens.ts` | Single source of truth — TypeScript constants |
| `frontend/config/icons.ts` | Central icon registry — all Lucide imports |
| `frontend/styles/tokens.css` | CSS custom properties for runtime theming |
| `frontend/tailwind.config.ts` | Tailwind theme extension consuming tokens |
| `docs/frontend/DESIGN_SYSTEM.md` | This document — usage guide |
| `frontend/utils/colorFromType.ts` | Utility that maps entity type string → token color |
| `frontend/utils/scoreToLabel.ts` | Utility that maps confidence score → high/medium/low label |
