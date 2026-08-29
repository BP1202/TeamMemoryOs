/**
 * Application-wide constants.
 * No hardcoded values inside components — reference these instead.
 */

// ─── App ──────────────────────────────────────────────────────────────────

export const APP_NAME = import.meta.env.VITE_APP_NAME ?? 'TeamMemoryOS';

// ─── API ──────────────────────────────────────────────────────────────────

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// ─── UI Behavior ──────────────────────────────────────────────────────────

/** Debounce delay (ms) for search inputs. */
export const DEBOUNCE_MS = 300;

/** Default page size for paginated lists. */
export const DEFAULT_PAGE_SIZE = 20;

/** Max items before enabling react-window virtualization. */
export const VIRTUALIZE_THRESHOLD = 100;

// ─── React Query stale times ──────────────────────────────────────────────

/** User/auth data — relatively static, 5 minutes. */
export const STALE_TIME_USER = 5 * 60 * 1000;

/** Memory entries — moderate churn, 2 minutes. */
export const STALE_TIME_MEMORY = 2 * 60 * 1000;

/** Knowledge graph entities — slow changing, 10 minutes. */
export const STALE_TIME_GRAPH = 10 * 60 * 1000;

/** AI chat responses — never stale (always fresh). */
export const STALE_TIME_CHAT = 0;

// ─── Feature flags ────────────────────────────────────────────────────────

export const ENABLE_GRAPH_DEBUG =
  import.meta.env.VITE_ENABLE_GRAPH_DEBUG === 'true';

export const ENABLE_AGENT_TIMELINE =
  import.meta.env.VITE_ENABLE_AGENT_TIMELINE !== 'false';

export const ENABLE_STREAMING_UI =
  import.meta.env.VITE_ENABLE_STREAMING_UI === 'true';
