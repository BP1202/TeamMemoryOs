/**
 * Client-side UI state types.
 * These are purely client-owned — never from API responses.
 */

// ─── Theme ─────────────────────────────────────────────────────────────────

export type Theme = 'dark' | 'light' | 'system';

// ─── Sidebar ───────────────────────────────────────────────────────────────

export interface SidebarState {
  isCollapsed: boolean;
}

// ─── Navigation ────────────────────────────────────────────────────────────

export interface NavItem {
  key: string;
  label: string;
  path: string;
  icon: string; // key of NavIcons
  badge?: string | number;
}

// ─── UI Store State ────────────────────────────────────────────────────────

export interface UIState {
  theme: Theme;
  sidebarCollapsed: boolean;
}

// ─── Component variants (shared) ──────────────────────────────────────────

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';
export type ButtonSize    = 'sm' | 'md' | 'lg' | 'icon';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info';

export type CardVariant = 'default' | 'elevated' | 'outline';
