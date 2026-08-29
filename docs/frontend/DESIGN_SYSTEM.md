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

## Files Reference

| File | Purpose |
|---|---|
| `frontend/config/design-tokens.ts` | Single source of truth — TypeScript constants |
| `frontend/styles/tokens.css` | CSS custom properties for runtime theming |
| `frontend/tailwind.config.ts` | Tailwind theme extension consuming tokens |
| `docs/frontend/DESIGN_SYSTEM.md` | This document — usage guide |
| `frontend/utils/colorFromType.ts` | Utility that maps entity type string → token color |
| `frontend/utils/scoreToLabel.ts` | Utility that maps confidence score → high/medium/low label |
