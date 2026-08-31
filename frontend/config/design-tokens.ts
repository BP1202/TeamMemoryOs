/**
 * TeamMemoryOS Design Token Registry
 *
 * This is the single source of truth for all visual values.
 *
 * Rules:
 *  - Never hardcode a color, spacing, shadow, or duration in a component.
 *  - Tailwind config consumes these values via tailwind.config.ts.
 *  - CSS variables in styles/tokens.css mirror these names exactly.
 *  - Framer Motion variants reference animation tokens from this file.
 *  - Tokens are immutable — `as const` is applied throughout.
 */

// ─── Colors ──────────────────────────────────────────────────────────────────

export const colors = {
  /**
   * Background surface layers from reference image:
   * Deep obsidian-violet canvas to elevated slate-purple cards.
   */
  surface: {
    base:     '#0F0C1B', // Root page canvas (deep midnight purple)
    default:  '#161327', // Cards, panels, sidebars
    elevated: '#211C3B', // Dropdowns, dialogs, active cards
    subtle:   '#2D264F', // Hover highlights, row backgrounds
    overlay:  'rgba(15, 12, 27, 0.85)', // Backdrop overlays
  },

  /**
   * Brand — Vibrant Electric Violet / Purple from reference dashboard.
   */
  brand: {
    default: '#A855F7',
    hover:   '#C084FC',
    muted:   '#6B21A8',
    subtle:  '#2E1065',
    ring:    'rgba(168, 85, 247, 0.5)', // Focus ring (with alpha)
  },

  /**
   * Semantic status colors matching reference charts & badges.
   */
  success: {
    default: '#22C55E', // Vivid mint/green
    muted:   '#14532D',
    subtle:  '#052E16',
  },
  warning: {
    default: '#F59E0B', // Amber
    muted:   '#78350F',
    subtle:  '#451A03',
  },
  danger: {
    default: '#F43F5E', // Vivid Rose/Coral
    muted:   '#881337',
    subtle:  '#4C0519',
  },
  info: {
    default: '#2DD4BF', // Vibrant Teal / Cyan
    muted:   '#134E4A',
    subtle:  '#042F2E',
  },

  /**
   * Text hierarchy tailored to dark purple theme.
   */
  text: {
    primary:   '#FFFFFF', // Main readable text
    secondary: '#C4BFDE', // Soft lavender secondary labels
    muted:     '#7B74A3', // Placeholders, disabled states
    inverse:   '#0F0C1B', // Text on light backgrounds
    link:      '#C084FC', // Inline links
    code:      '#E9D5FF', // Inline code tokens
  },

  /**
   * Border and divider colors with soft purple tint.
   */
  border: {
    default: '#2D264E',
    subtle:  '#1E1938',
    focus:   '#A855F7',
    danger:  '#F43F5E',
  },

  /**
   * Confidence banding for AI explainability components.
   */
  confidence: {
    high:        '#22C55E',
    highMuted:   '#14532D',
    medium:      '#F59E0B',
    mediumMuted: '#78350F',
    low:         '#F43F5E',
    lowMuted:    '#881337',
  },

  /**
   * Entity type colors for Knowledge Graph nodes.
   */
  entityType: {
    person:       '#A855F7', // Violet
    technology:   '#2DD4BF', // Cyan / Teal
    project:      '#22C55E', // Emerald
    decision:     '#F59E0B', // Amber
    concept:      '#E879F9', // Magenta / Pink
    organization: '#FB923C', // Orange
    default:      '#C4BFDE', // Lavender slate
  },

  /**
   * Memory entry type colors for badge rendering.
   */
  memoryType: {
    DECISION:      '#F59E0B',
    CODE:          '#2DD4BF',
    DISCUSSION:    '#A855F7',
    DOCUMENTATION: '#22C55E',
    INCIDENT:      '#F43F5E',
  },
} as const;

// ─── Typography ──────────────────────────────────────────────────────────────

export const typography = {
  /**
   * Font family stacks.
   * Inter for UI text; JetBrains Mono for code, terminal output, stack traces.
   */
  fontFamily: {
    sans: 'Inter, system-ui, sans-serif',
    mono: '"JetBrains Mono", "Fira Code", ui-monospace, monospace',
  },

  /**
   * Font size scale with paired line-height.
   * Format: [fontSize, lineHeight]
   */
  fontSize: {
    xs:    ['0.75rem',  { lineHeight: '1rem'    }] as const, // 12px — labels, badges
    sm:    ['0.875rem', { lineHeight: '1.25rem' }] as const, // 14px — body secondary
    base:  ['1rem',     { lineHeight: '1.5rem'  }] as const, // 16px — body primary
    lg:    ['1.125rem', { lineHeight: '1.75rem' }] as const, // 18px — subheadings
    xl:    ['1.25rem',  { lineHeight: '1.75rem' }] as const, // 20px — section headings
    '2xl': ['1.5rem',   { lineHeight: '2rem'    }] as const, // 24px — page headings
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }] as const, // 30px — hero headings
    '4xl': ['2.25rem',  { lineHeight: '2.5rem'  }] as const, // 36px — display text
  },

  /**
   * Font weight constants.
   */
  fontWeight: {
    normal:   '400',
    medium:   '500',
    semibold: '600',
    bold:     '700',
  },

  /**
   * Letter spacing scale.
   */
  letterSpacing: {
    tighter: '-0.05em',
    tight:   '-0.025em',
    normal:  '0em',
    wide:    '0.025em',
    wider:   '0.05em',
    widest:  '0.1em',
  },

  /**
   * Semantic text style roles.
   * These document intent — combine size + weight + tracking.
   * Reference when creating new Tailwind component classes.
   */
  textStyles: {
    display:   { size: '4xl', weight: 'bold',     tracking: 'tight'  },
    heading:   { size: '3xl', weight: 'bold',     tracking: 'tight'  },
    title:     { size: '2xl', weight: 'semibold', tracking: 'normal' },
    subtitle:  { size: 'xl',  weight: 'medium',   tracking: 'normal' },
    body:      { size: 'base',weight: 'normal',   tracking: 'normal' },
    bodySmall: { size: 'sm',  weight: 'normal',   tracking: 'normal' },
    caption:   { size: 'xs',  weight: 'normal',   tracking: 'wide'   },
    code:      { size: 'sm',  weight: 'normal',   tracking: 'normal' },
    label:     { size: 'xs',  weight: 'medium',   tracking: 'wider'  },
  },
} as const;

// ─── Spacing ─────────────────────────────────────────────────────────────────

/**
 * 4px base unit spacing scale.
 * Aligns exactly with Tailwind's default spacing (1 unit = 4px).
 *
 * Semantic aliases provide named intent beyond raw numbers.
 */
export const spacing = {
  px:   '1px',
  0.5:  '2px',
  1:    '4px',
  1.5:  '6px',
  2:    '8px',
  2.5:  '10px',
  3:    '12px',
  3.5:  '14px',
  4:    '16px',
  5:    '20px',
  6:    '24px',
  7:    '28px',
  8:    '32px',
  9:    '36px',
  10:   '40px',
  11:   '44px',
  12:   '48px',
  14:   '56px',
  16:   '64px',
  20:   '80px',
  24:   '96px',
  28:   '112px',
  32:   '128px',
  36:   '144px',
  40:   '160px',
  48:   '192px',
  56:   '224px',
  64:   '256px',

  // ── Semantic layout aliases ──
  inputX:          '12px',  // Input horizontal padding
  inputY:          '8px',   // Input vertical padding
  cardPadding:     '24px',  // Standard card internal padding
  pagePadding:     '32px',  // Page outer horizontal padding
  sectionGap:      '40px',  // Gap between major page sections
  sidebarWidth:    '240px', // Sidebar width when expanded
  sidebarCollapsed:'64px',  // Sidebar width when collapsed
  topbarHeight:    '56px',  // Topbar fixed height
} as const;

// ─── Border Radius ────────────────────────────────────────────────────────────

export const radius = {
  none: '0px',
  xs:   '2px',    // Subtle rounding (code inline badge)
  sm:   '4px',    // Small elements (tags, small badges)
  md:   '8px',    // Buttons, inputs, cards
  lg:   '12px',   // Larger cards, dialogs
  xl:   '16px',   // Panels, drawers
  '2xl':'24px',   // Large featured cards
  full: '9999px', // Pills, circular avatars, toggles
} as const;

// ─── Shadows / Elevation ──────────────────────────────────────────────────────

/**
 * Elevation shadows — designed for dark surfaces only.
 *
 * Elevation ladder:
 *   none → sm → md → lg → xl
 *
 * Use the lowest elevation that creates sufficient visual separation.
 */
export const shadows = {
  none:   'none',
  sm:     '0 1px 2px rgba(0, 0, 0, 0.4)',
  md:     '0 4px 12px rgba(0, 0, 0, 0.5)',
  lg:     '0 8px 24px rgba(0, 0, 0, 0.6)',
  xl:     '0 16px 48px rgba(0, 0, 0, 0.7)',

  // ── Semantic shadows ──
  glow:   '0 0 20px rgba(99, 102, 241, 0.2)',  // Brand glow — active/focus states
  danger: '0 0 12px rgba(239, 68, 68, 0.25)',  // Error focus ring glow
  card:   '0 2px 8px rgba(0, 0, 0, 0.45)',     // Default card elevation
  dialog: '0 12px 40px rgba(0, 0, 0, 0.65)',   // Modal / dialog elevation
  drawer: '4px 0 24px rgba(0, 0, 0, 0.5)',     // Side drawer elevation
} as const;

// ─── Z-Index ─────────────────────────────────────────────────────────────────

/**
 * Z-index stacking layers.
 *
 * Rule: Never use an arbitrary z-index value in a component.
 * Always reference this table.
 */
export const zIndex = {
  base:    0,  // Default document flow
  raised:  1,  // Slightly elevated (table row hover, sticky headers)
  sidebar: 20, // Fixed sidebar panel
  topbar:  30, // Fixed topbar (always above sidebar)
  drawer:  40, // Slide-in detail drawer
  modal:   50, // Dialogs and modals
  popover: 60, // Dropdowns, popovers (above modals)
  tooltip: 70, // Tooltips (topmost interactive layer)
  toast:   80, // Toast notifications (always on top)
} as const;

// ─── Animation ────────────────────────────────────────────────────────────────

/**
 * Animation timing and easing tokens.
 *
 * Rules:
 *  - Use 'fast' for hover/focus micro-interactions.
 *  - Use 'medium' for panel entrances, dialogs, drawers.
 *  - Use 'slow' for full-page transitions only.
 *  - All Framer Motion variants must check useReducedMotion().
 *    When reduced-motion is active, pass duration: 0.
 */
export const animation = {
  /**
   * Duration values in milliseconds (for Framer Motion).
   */
  duration: {
    instant:  0,   // Reduced-motion fallback — no animation
    fast:     150, // Hover states, focus rings, button press
    medium:   200, // Panel entrances, dialog open/close
    slow:     300, // Page transitions, complex layout shifts
    verySlow: 500, // Reserved for deliberate emphasis only
  },

  /**
   * CSS duration strings (for Tailwind transition utilities or inline styles).
   */
  durationCSS: {
    fast:     '150ms',
    medium:   '200ms',
    slow:     '300ms',
    verySlow: '500ms',
  },

  /**
   * Easing curves as CSS cubic-bezier strings.
   */
  easing: {
    easeOut:   'cubic-bezier(0.0, 0.0, 0.2, 1)',    // Decelerating — best for enters
    easeIn:    'cubic-bezier(0.4, 0.0, 1, 1)',      // Accelerating — best for exits
    easeInOut: 'cubic-bezier(0.4, 0.0, 0.2, 1)',    // Standard — most transitions
    spring:    'cubic-bezier(0.34, 1.56, 0.64, 1)', // Slight overshoot — interactive
  },

  /**
   * Framer Motion named easing equivalents.
   * Pass as the `ease` prop in motion transition objects.
   */
  framerEasing: {
    easeOut:   'easeOut'  as const,
    easeIn:    'easeIn'   as const,
    easeInOut: 'easeInOut'as const,
    spring:    [0.34, 1.56, 0.64, 1] as [number, number, number, number],
  },

  /**
   * Canonical Framer Motion variant patterns.
   *
   * Usage:
   *   import { animation } from '@/config/design-tokens';
   *   <motion.div variants={animation.variants.fadeUp} initial="hidden" animate="visible" />
   *
   * Always wrap with useReducedMotion() check and pass
   * transition: { duration: 0 } when reduced-motion is active.
   */
  variants: {
    /** Fade + subtle upward slide. Standard page/section entrance. */
    fadeUp: {
      hidden:  { opacity: 0, y: 8 },
      visible: { opacity: 1, y: 0,  transition: { duration: 0.2,  ease: 'easeOut' } },
      exit:    { opacity: 0, y: 4,  transition: { duration: 0.15, ease: 'easeIn'  } },
    },

    /** Fade only. Lightweight for small elements. */
    fadeIn: {
      hidden:  { opacity: 0 },
      visible: { opacity: 1, transition: { duration: 0.2,  ease: 'easeOut' } },
      exit:    { opacity: 0, transition: { duration: 0.15, ease: 'easeIn'  } },
    },

    /** Slide in from right. Drawers, side panels, inspector panels. */
    slideRight: {
      hidden:  { opacity: 0, x: 16 },
      visible: { opacity: 1, x: 0,  transition: { duration: 0.18, ease: 'easeOut' } },
      exit:    { opacity: 0, x: 16, transition: { duration: 0.15, ease: 'easeIn'  } },
    },

    /** Slide up from bottom. Mobile sheets, toast notifications. */
    slideUp: {
      hidden:  { opacity: 0, y: 16 },
      visible: { opacity: 1, y: 0,  transition: { duration: 0.2,  ease: 'easeOut' } },
      exit:    { opacity: 0, y: 16, transition: { duration: 0.15, ease: 'easeIn'  } },
    },

    /** Scale + fade. Dialogs and modals. */
    scaleIn: {
      hidden:  { opacity: 0, scale: 0.96 },
      visible: { opacity: 1, scale: 1,    transition: { duration: 0.2,  ease: 'easeOut' } },
      exit:    { opacity: 0, scale: 0.96, transition: { duration: 0.15, ease: 'easeIn'  } },
    },

    /** Individual list item. Use with staggerContainer on parent. */
    listItem: {
      hidden:  { opacity: 0, y: 4 },
      visible: { opacity: 1, y: 0, transition: { duration: 0.15, ease: 'easeOut' } },
    },

    /** Parent wrapper for staggered list items. */
    staggerContainer: {
      hidden:  {},
      visible: { transition: { staggerChildren: 0.05, delayChildren: 0.05 } },
    },
  },
} as const;

// ─── Breakpoints ──────────────────────────────────────────────────────────────

/**
 * Responsive breakpoints — desktop-first layout strategy.
 *
 * Design target: 1440px desktop. Adapt downward.
 * Minimum supported viewport: 768px (tablet).
 *
 * These mirror Tailwind's default breakpoints so custom CSS
 * and Tailwind utilities always share the same thresholds.
 */
export const breakpoints = {
  xs:   '480px',  // Large mobile (not officially supported — graceful degradation)
  sm:   '640px',  // Small tablet
  md:   '768px',  // Tablet — minimum supported viewport
  lg:   '1024px', // Laptop
  xl:   '1280px', // Desktop
  '2xl':'1536px', // Wide desktop / 4K
} as const;

// ─── Composite Export ─────────────────────────────────────────────────────────

// ─── Component Tokens ────────────────────────────────────────────────────────

/**
 * Component token map.
 *
 * Each entry defines the exact design token values that a specific component
 * variant applies. These are not Tailwind classes — they are the raw values
 * that Tailwind classes must resolve to.
 *
 * Rules:
 *  - Never hardcode values inside a component. Reference this map or the CSS
 *    variables derived from it (--component-<name>-<prop>).
 *  - Every variant maps to tokens already defined above in this file.
 *  - Adding a new variant means: add here → add CSS vars → update Tailwind.
 */
export const componentTokens = {

  // ── Button ─────────────────────────────────────────────────────────────────

  button: {
    /**
     * Primary: filled brand background. Main call-to-action.
     */
    primary: {
      bg:           colors.brand.default,
      bgHover:      colors.brand.hover,
      bgActive:     colors.brand.muted,
      bgDisabled:   colors.surface.elevated,
      text:         '#ffffff',
      textDisabled: colors.text.muted,
      border:       'transparent',
      ring:         colors.brand.ring,
      shadow:       shadows.glow,
    },

    /**
     * Secondary: subtle surface background with visible border. Secondary actions.
     */
    secondary: {
      bg:           colors.surface.elevated,
      bgHover:      colors.surface.subtle,
      bgActive:     colors.surface.subtle,
      bgDisabled:   colors.surface.elevated,
      text:         colors.text.primary,
      textDisabled: colors.text.muted,
      border:       colors.border.default,
      borderHover:  colors.brand.default,
      ring:         colors.brand.ring,
      shadow:       shadows.none,
    },

    /**
     * Ghost: transparent background. Tertiary or icon-adjacent actions.
     */
    ghost: {
      bg:           'transparent',
      bgHover:      colors.surface.subtle,
      bgActive:     colors.surface.elevated,
      bgDisabled:   'transparent',
      text:         colors.text.secondary,
      textHover:    colors.text.primary,
      textDisabled: colors.text.muted,
      border:       'transparent',
      ring:         colors.brand.ring,
      shadow:       shadows.none,
    },

    /**
     * Destructive: danger-colored. Irreversible actions (delete, revoke).
     */
    destructive: {
      bg:           colors.danger.default,
      bgHover:      '#f87171',             // danger lightened one step
      bgActive:     colors.danger.muted,
      bgDisabled:   colors.surface.elevated,
      text:         '#ffffff',
      textDisabled: colors.text.muted,
      border:       'transparent',
      ring:         'rgba(239, 68, 68, 0.4)',
      shadow:       shadows.danger,
    },

    // Shared across all variants
    shared: {
      borderRadius:    radius.md,
      fontWeight:      typography.fontWeight.medium,
      fontSizeSm:      typography.fontSize.sm[0],
      fontSizeMd:      typography.fontSize.base[0],
      paddingXSm:      spacing[3],
      paddingYSm:      spacing[1.5],
      paddingXMd:      spacing[4],
      paddingYMd:      spacing[2],
      transitionDuration: animation.durationCSS.medium,
      transitionEasing:   animation.easing.easeInOut,
    },
  },

  // ── Card ───────────────────────────────────────────────────────────────────

  card: {
    /**
     * Default: standard surface panel. Most cards use this.
     */
    default: {
      bg:           colors.surface.default,
      border:       colors.border.default,
      borderRadius: radius.lg,
      shadow:       shadows.card,
      padding:      spacing.cardPadding,
    },

    /**
     * Elevated: pops above surrounding content. Dialogs, callout cards.
     */
    elevated: {
      bg:           colors.surface.elevated,
      border:       colors.border.subtle,
      borderRadius: radius.lg,
      shadow:       shadows.md,
      padding:      spacing.cardPadding,
    },

    /**
     * Outline: transparent background with visible border. Secondary cards,
     * inactive states, selectable items.
     */
    outline: {
      bg:           'transparent',
      bgHover:      colors.surface.subtle,
      border:       colors.border.default,
      borderHover:  colors.brand.default,
      borderRadius: radius.lg,
      shadow:       shadows.none,
      padding:      spacing.cardPadding,
    },
  },

  // ── Input ──────────────────────────────────────────────────────────────────

  input: {
    /**
     * Default: resting state.
     */
    default: {
      bg:           colors.surface.elevated,
      border:       colors.border.default,
      borderRadius: radius.md,
      text:         colors.text.primary,
      placeholder:  colors.text.muted,
      paddingX:     spacing.inputX,
      paddingY:     spacing.inputY,
      fontSize:     typography.fontSize.sm[0],
      shadow:       shadows.none,
    },

    /**
     * Focus: keyboard or pointer focus active.
     */
    focus: {
      bg:           colors.surface.elevated,
      border:       colors.border.focus,
      ring:         colors.brand.ring,
      shadow:       shadows.glow,
    },

    /**
     * Error: validation failure state.
     */
    error: {
      bg:           colors.surface.elevated,
      border:       colors.border.danger,
      ring:         'rgba(239, 68, 68, 0.3)',
      text:         colors.text.primary,
      labelText:    colors.danger.default,
      hintText:     colors.danger.default,
      shadow:       shadows.danger,
    },

    /**
     * Disabled: non-interactive state.
     */
    disabled: {
      bg:           colors.surface.subtle,
      border:       colors.border.subtle,
      text:         colors.text.muted,
      cursor:       'not-allowed',
    },
  },

  // ── Badge ──────────────────────────────────────────────────────────────────

  badge: {
    /**
     * Success: positive outcome, healthy status.
     */
    success: {
      bg:           colors.success.muted,
      text:         colors.success.default,
      border:       colors.success.muted,
      borderRadius: radius.full,
    },

    /**
     * Warning: degraded, needs attention.
     */
    warning: {
      bg:           colors.warning.muted,
      text:         colors.warning.default,
      border:       colors.warning.muted,
      borderRadius: radius.full,
    },

    /**
     * Danger: failure, error, destructive state.
     */
    danger: {
      bg:           colors.danger.muted,
      text:         colors.danger.default,
      border:       colors.danger.muted,
      borderRadius: radius.full,
    },

    /**
     * Info: neutral informational label.
     */
    info: {
      bg:           colors.info.muted,
      text:         colors.info.default,
      border:       colors.info.muted,
      borderRadius: radius.full,
    },

    /**
     * Default: generic / uncategorized label.
     */
    default: {
      bg:           colors.surface.elevated,
      text:         colors.text.secondary,
      border:       colors.border.default,
      borderRadius: radius.full,
    },

    // Shared across all badge variants
    shared: {
      fontWeight:  typography.fontWeight.medium,
      fontSize:    typography.fontSize.xs[0],
      paddingX:    spacing[2],
      paddingY:    spacing[0.5],
      lineHeight:  '1rem',
    },
  },

  // ── AI Explainability Components ───────────────────────────────────────────
  //
  // These tokens are used exclusively by features/explainability/ components.
  // They must never be used inside general UI primitives.

  ai: {
    /**
     * Confidence badge — high (score > 0.75).
     */
    confidenceHigh: {
      bg:           colors.confidence.highMuted,
      text:         colors.confidence.high,
      border:       colors.confidence.highMuted,
      icon:         colors.confidence.high,
      borderRadius: radius.full,
    },

    /**
     * Confidence badge — medium (score 0.5–0.75).
     */
    confidenceMedium: {
      bg:           colors.confidence.mediumMuted,
      text:         colors.confidence.medium,
      border:       colors.confidence.mediumMuted,
      icon:         colors.confidence.medium,
      borderRadius: radius.full,
    },

    /**
     * Confidence badge — low (score < 0.5).
     */
    confidenceLow: {
      bg:           colors.confidence.lowMuted,
      text:         colors.confidence.low,
      border:       colors.confidence.lowMuted,
      icon:         colors.confidence.low,
      borderRadius: radius.full,
    },

    /**
     * Retrieval mode tag — semantic (vector similarity only).
     */
    retrievalSemantic: {
      bg:           colors.info.muted,
      text:         colors.info.default,
      border:       colors.info.muted,
      borderRadius: radius.full,
    },

    /**
     * Retrieval mode tag — hybrid (vector + knowledge graph).
     */
    retrievalHybrid: {
      bg:           colors.brand.muted,
      text:         colors.brand.hover,
      border:       colors.brand.muted,
      borderRadius: radius.full,
    },

    /**
     * Retrieval mode tag — engineering (code-aware copilot).
     */
    retrievalEngineering: {
      bg:           colors.warning.muted,
      text:         colors.warning.default,
      border:       colors.warning.muted,
      borderRadius: radius.full,
    },

    /**
     * Citation card surface.
     */
    citationCard: {
      bg:           colors.surface.elevated,
      border:       colors.border.default,
      borderLeft:   colors.brand.default,
      borderLeftWidth: '3px',
      borderRadius: radius.md,
      text:         colors.text.primary,
      metaText:     colors.text.secondary,
    },

    /**
     * Graph path breadcrumb item.
     */
    graphPathItem: {
      text:         colors.text.secondary,
      textActive:   colors.brand.hover,
      separator:    colors.text.muted,
      bg:           'transparent',
      bgActive:     colors.brand.subtle,
      borderRadius: radius.sm,
    },

    // Shared across all AI component tokens
    shared: {
      fontWeight:  typography.fontWeight.medium,
      fontSize:    typography.fontSize.xs[0],
      paddingX:    spacing[2],
      paddingY:    spacing[0.5],
    },
  },
} as const;

export type ComponentTokens = typeof componentTokens;

// ─── Composite export ─────────────────────────────────────────────────────────

/**
 * Full token registry.
 *
 * Import `tokens` when consuming values in TypeScript
 * (e.g. Framer Motion inline styles, canvas rendering, tests).
 *
 * For Tailwind classes, use the Tailwind config which maps these tokens.
 * For CSS, use the variables defined in styles/tokens.css.
 */
export const tokens = {
  colors,
  typography,
  spacing,
  radius,
  shadows,
  zIndex,
  animation,
  breakpoints,
  component: componentTokens,
} as const;

export type Tokens        = typeof tokens;
export type ColorTokens   = typeof colors;
export type SpacingTokens = typeof spacing;

export default tokens;
