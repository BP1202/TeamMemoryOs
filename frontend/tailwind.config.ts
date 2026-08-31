import type { Config } from 'tailwindcss';
import { tokens } from './config/design-tokens';

/**
 * TeamMemoryOS Tailwind CSS Configuration
 *
 * This file consumes values exclusively from frontend/config/design-tokens.ts.
 * No color, spacing, radius, shadow, or animation value is hardcoded here.
 *
 * Rules:
 *   - Never add a raw hex value to this config. Add it to design-tokens.ts first.
 *   - CSS variables (var(--...)) are used as values so that runtime theme
 *     switching remains possible without a rebuild.
 *   - All token groups map to their corresponding Tailwind extension keys.
 *
 * Source of truth: frontend/config/design-tokens.ts
 * CSS variables:   frontend/styles/tokens.css
 */

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './features/**/*.{ts,tsx}',
    './layouts/**/*.{ts,tsx}',
    './providers/**/*.{ts,tsx}',
    './config/**/*.{ts,tsx}',
  ],

  darkMode: 'class',

  theme: {
    // ── Override defaults only for values with project-specific meaning ──

    screens: {
      xs:    tokens.breakpoints.xs,
      sm:    tokens.breakpoints.sm,
      md:    tokens.breakpoints.md,
      lg:    tokens.breakpoints.lg,
      xl:    tokens.breakpoints.xl,
      '2xl': tokens.breakpoints['2xl'],
    },

    extend: {
      // ── Colors ──────────────────────────────────────────────────────────
      // Values reference CSS variables so the palette is theme-switchable.
      // Tailwind class: bg-surface-default, text-brand, border-border, etc.

      colors: {
        // Surface backgrounds
        surface: {
          base:     'var(--color-surface-base)',
          DEFAULT:  'var(--color-surface-default)',
          elevated: 'var(--color-surface-elevated)',
          subtle:   'var(--color-surface-subtle)',
          overlay:  'var(--color-surface-overlay)',
        },

        // Brand — Indigo
        brand: {
          DEFAULT: 'var(--color-brand-default)',
          hover:   'var(--color-brand-hover)',
          muted:   'var(--color-brand-muted)',
          subtle:  'var(--color-brand-subtle)',
          ring:    'var(--color-brand-ring)',
        },

        // Semantic status
        success: {
          DEFAULT: 'var(--color-success-default)',
          muted:   'var(--color-success-muted)',
          subtle:  'var(--color-success-subtle)',
        },
        warning: {
          DEFAULT: 'var(--color-warning-default)',
          muted:   'var(--color-warning-muted)',
          subtle:  'var(--color-warning-subtle)',
        },
        danger: {
          DEFAULT: 'var(--color-danger-default)',
          muted:   'var(--color-danger-muted)',
          subtle:  'var(--color-danger-subtle)',
        },
        info: {
          DEFAULT: 'var(--color-info-default)',
          muted:   'var(--color-info-muted)',
          subtle:  'var(--color-info-subtle)',
        },

        // Text
        text: {
          primary:   'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted:     'var(--color-text-muted)',
          inverse:   'var(--color-text-inverse)',
          link:      'var(--color-text-link)',
          code:      'var(--color-text-code)',
        },

        // Borders
        border: {
          DEFAULT: 'var(--color-border-default)',
          subtle:  'var(--color-border-subtle)',
          focus:   'var(--color-border-focus)',
          danger:  'var(--color-border-danger)',
        },

        // Confidence banding (AI explainability)
        confidence: {
          high:          'var(--color-confidence-high)',
          'high-muted':  'var(--color-confidence-high-muted)',
          medium:        'var(--color-confidence-medium)',
          'medium-muted':'var(--color-confidence-medium-muted)',
          low:           'var(--color-confidence-low)',
          'low-muted':   'var(--color-confidence-low-muted)',
        },

        // Entity type colors (Knowledge Graph)
        entity: {
          person:       'var(--color-entity-person)',
          technology:   'var(--color-entity-technology)',
          project:      'var(--color-entity-project)',
          decision:     'var(--color-entity-decision)',
          concept:      'var(--color-entity-concept)',
          organization: 'var(--color-entity-organization)',
          default:      'var(--color-entity-default)',
        },

        // Memory type colors
        memory: {
          decision:      'var(--color-memory-decision)',
          code:          'var(--color-memory-code)',
          discussion:    'var(--color-memory-discussion)',
          documentation: 'var(--color-memory-documentation)',
          incident:      'var(--color-memory-incident)',
        },
      },

      // ── Typography ───────────────────────────────────────────────────────

      fontFamily: {
        sans: tokens.typography.fontFamily.sans,
        mono: tokens.typography.fontFamily.mono,
      },

      fontSize: {
        xs:   tokens.typography.fontSize.xs,
        sm:   tokens.typography.fontSize.sm,
        base: tokens.typography.fontSize.base,
        lg:   tokens.typography.fontSize.lg,
        xl:   tokens.typography.fontSize.xl,
        '2xl':tokens.typography.fontSize['2xl'],
        '3xl':tokens.typography.fontSize['3xl'],
        '4xl':tokens.typography.fontSize['4xl'],
      },

      fontWeight: {
        normal:   tokens.typography.fontWeight.normal,
        medium:   tokens.typography.fontWeight.medium,
        semibold: tokens.typography.fontWeight.semibold,
        bold:     tokens.typography.fontWeight.bold,
      },

      letterSpacing: {
        tighter: tokens.typography.letterSpacing.tighter,
        tight:   tokens.typography.letterSpacing.tight,
        normal:  tokens.typography.letterSpacing.normal,
        wide:    tokens.typography.letterSpacing.wide,
        wider:   tokens.typography.letterSpacing.wider,
        widest:  tokens.typography.letterSpacing.widest,
      },

      // ── Spacing ──────────────────────────────────────────────────────────
      // Tailwind's default spacing is already 4px-based, so we only add
      // project-specific semantic aliases beyond Tailwind's default scale.

      spacing: {
        'sidebar':           tokens.spacing.sidebarW,
        'sidebar-collapsed': tokens.spacing.sidebarCollapsedW,
        'topbar':            tokens.spacing.topbarH,
        'card':              tokens.spacing.cardPadding,
        'page':              tokens.spacing.pagePadding,
        'section':           tokens.spacing.sectionGap,
        'input-x':           tokens.spacing.inputX,
        'input-y':           tokens.spacing.inputY,
      },

      // ── Border Radius ─────────────────────────────────────────────────────

      borderRadius: {
        none: tokens.radius.none,
        xs:   tokens.radius.xs,
        sm:   tokens.radius.sm,
        DEFAULT: tokens.radius.md,
        md:   tokens.radius.md,
        lg:   tokens.radius.lg,
        xl:   tokens.radius.xl,
        '2xl':tokens.radius['2xl'],
        full: tokens.radius.full,
      },

      // ── Shadows ───────────────────────────────────────────────────────────

      boxShadow: {
        none:   tokens.shadows.none,
        sm:     tokens.shadows.sm,
        DEFAULT:tokens.shadows.md,
        md:     tokens.shadows.md,
        lg:     tokens.shadows.lg,
        xl:     tokens.shadows.xl,
        glow:   tokens.shadows.glow,
        danger: tokens.shadows.danger,
        card:   tokens.shadows.card,
        dialog: tokens.shadows.dialog,
        drawer: tokens.shadows.drawer,
      },

      // ── Z-Index ───────────────────────────────────────────────────────────

      zIndex: {
        base:    String(tokens.zIndex.base),
        raised:  String(tokens.zIndex.raised),
        sidebar: String(tokens.zIndex.sidebar),
        topbar:  String(tokens.zIndex.topbar),
        drawer:  String(tokens.zIndex.drawer),
        modal:   String(tokens.zIndex.modal),
        popover: String(tokens.zIndex.popover),
        tooltip: String(tokens.zIndex.tooltip),
        toast:   String(tokens.zIndex.toast),
      },

      // ── Animation ─────────────────────────────────────────────────────────

      transitionDuration: {
        fast:      String(tokens.animation.duration.fast),
        medium:    String(tokens.animation.duration.medium),
        slow:      String(tokens.animation.duration.slow),
        'very-slow': String(tokens.animation.duration.verySlow),
      },

      transitionTimingFunction: {
        'ease-out':    tokens.animation.easing.easeOut,
        'ease-in':     tokens.animation.easing.easeIn,
        'ease-in-out': tokens.animation.easing.easeInOut,
        spring:        tokens.animation.easing.spring,
      },

      // ── Keyframes for skeleton pulse ──────────────────────────────────────

      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
        'fade-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-in-right': {
          '0%':   { transform: 'translateX(16px)', opacity: '0' },
          '100%': { transform: 'translateX(0)',    opacity: '1' },
        },
        'slide-in-up': {
          '0%':   { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',   opacity: '1' },
        },
      },

      animation: {
        pulse:          `pulse ${tokens.animation.durationCSS.slow} ${tokens.animation.easing.easeInOut} infinite`,
        'fade-in':      `fade-in ${tokens.animation.durationCSS.medium} ${tokens.animation.easing.easeOut}`,
        'slide-right':  `slide-in-right ${tokens.animation.durationCSS.medium} ${tokens.animation.easing.easeOut}`,
        'slide-up':     `slide-in-up ${tokens.animation.durationCSS.medium} ${tokens.animation.easing.easeOut}`,
      },
    },
  },

  plugins: [],
};

export default config;
