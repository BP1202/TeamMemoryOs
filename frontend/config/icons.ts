/**
 * TeamMemoryOS Icon Registry
 *
 * Central registry for all Lucide React icons used in the application.
 *
 * Rules:
 *  - Import icons exclusively from this file — never import Lucide directly
 *    inside feature components or UI primitives.
 *  - Icons are grouped by semantic domain.
 *  - Every icon reference in JSX must resolve to a key in this registry.
 *  - Use the `iconSize` constants for consistent sizing.
 *  - Adding a new icon: import it here, add to the appropriate group, done.
 *
 * Usage:
 *   import { NavIcons, StatusIcons, AIIcons } from '@/config/icons';
 *   <NavIcons.Memory className="h-5 w-5" />
 *
 * Source of truth: this file.
 * Documentation:   docs/frontend/DESIGN_SYSTEM.md — Icon Registry section.
 */

import {
  // Navigation
  LayoutDashboard,
  Database,
  Network,
  MessageSquare,
  Bot,
  Settings,

  // Memory types
  Lightbulb,
  AlertTriangle,
  BookOpen,
  Code2,
  MessagesSquare,

  // Entity types
  User,
  Cpu,
  GitBranch,
  Server,
  Plug,
  GitPullRequest,
  GitBranchPlus,

  // Status
  CheckCircle2,
  AlertCircle,
  XCircle,
  Info,
  Clock,

  // AI Explainability
  Quote,
  BarChart2,
  Waypoints,
  Merge,
  Sparkles,

  // General utility (not in a named group but exported for use)
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  X,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  ExternalLink,
  Copy,
  Loader2,
  Eye,
  EyeOff,
  ArrowRight,
  RefreshCw,
  Trash2,
  Pencil,
  ZoomIn,
  ZoomOut,
  Maximize2,
  PanelLeft,
  LogOut,
  Menu,
} from 'lucide-react';

import type { LucideIcon } from 'lucide-react';

// ─── Icon Size Constants ──────────────────────────────────────────────────────
/**
 * Standard icon sizes.
 * Pass as Tailwind classes: `className={iconSize.nav}`
 *
 * inline  → 16px — inline text, table cells, dense lists
 * button  → 20px — standalone button icons, action triggers
 * nav     → 20px — sidebar navigation items
 * heading → 24px — page/section heading icons, empty state icons
 * feature → 32px — large decorative / feature illustration icons
 */
export const iconSize = {
  inline:  'h-4 w-4',  // 16px
  button:  'h-5 w-5',  // 20px
  nav:     'h-5 w-5',  // 20px
  heading: 'h-6 w-6',  // 24px
  feature: 'h-8 w-8',  // 32px
} as const;

export type IconSize = keyof typeof iconSize;

// ─── Navigation Icons ─────────────────────────────────────────────────────────
/**
 * Icons used in the sidebar, topbar, and breadcrumbs.
 * Keys match the route/feature name used in config/navigation.ts.
 */
export const NavIcons = {
  /** `/` — Dashboard overview */
  Dashboard: LayoutDashboard,

  /** `/memory` — Memory Workspace */
  Memory: Database,

  /** `/graph` — Knowledge Graph Viewer */
  Graph: Network,

  /** `/chat` — AI Chat & Retrieval Workspace */
  Chat: MessageSquare,

  /** `/agents` — Multi-Agent Workspace */
  Agents: Bot,

  /** `/settings` — Settings (future) */
  Settings,
} as const satisfies Record<string, LucideIcon>;

// ─── Memory Type Icons ────────────────────────────────────────────────────────
/**
 * Icons for MemoryTypeBadge and MemoryTable.
 * Keys match backend MemoryEntry.memory_type enum values exactly.
 */
export const MemoryTypeIcons = {
  /** Engineering or product decision captured in memory */
  DECISION: Lightbulb,

  /** Production incident or post-mortem */
  INCIDENT: AlertTriangle,

  /** Reference documentation, ADRs, runbooks */
  DOCUMENTATION: BookOpen,

  /** Code snippet, implementation note, or code review */
  CODE: Code2,

  /** Team discussion, meeting notes, Slack thread */
  DISCUSSION: MessagesSquare,
} as const satisfies Record<string, LucideIcon>;

// ─── Entity Type Icons ────────────────────────────────────────────────────────
/**
 * Icons for Knowledge Graph entity nodes and EntityInspectorPanel.
 * Keys match backend Entity.entity_type values.
 */
export const EntityTypeIcons = {
  /** Human contributor or stakeholder */
  person: User,

  /** Technology, framework, language, or tool */
  technology: Cpu,

  /** Git repository */
  repository: GitBranch,

  /** Deployed service or microservice */
  service: Server,

  /** External API or integration */
  api: Plug,

  /** Pull request */
  pull_request: GitPullRequest,

  /** Git branch */
  branch: GitBranchPlus,
} as const satisfies Record<string, LucideIcon>;

// ─── Status Icons ─────────────────────────────────────────────────────────────
/**
 * Icons for health widgets, badges, and status indicators.
 * Always pair with a text label — never use color alone to convey status.
 */
export const StatusIcons = {
  /** Operation succeeded / system healthy */
  success: CheckCircle2,

  /** Degraded / needs attention */
  warning: AlertCircle,

  /** Failed / unavailable */
  error: XCircle,

  /** Neutral informational */
  info: Info,

  /** In progress / queued */
  pending: Clock,
} as const satisfies Record<string, LucideIcon>;

// ─── AI Explainability Icons ──────────────────────────────────────────────────
/**
 * Icons for features/explainability/ components.
 * These icons appear on every AI response surface alongside the
 * explainability fields mandated by the AI UI Contract.
 */
export const AIIcons = {
  /** CitationPanel — sources retrieved from memory */
  citation: Quote,

  /** ConfidenceBadge — numeric confidence score from Granite */
  confidence: BarChart2,

  /** GraphPathPanel — entity traversal chain from Knowledge Graph */
  graphPath: Waypoints,

  /** RetrievalModeTag (hybrid) — vector + graph retrieval */
  hybridRetrieval: Merge,

  /** IBM Granite model attribution */
  granite: Sparkles,
} as const satisfies Record<string, LucideIcon>;

// ─── Utility Icons ────────────────────────────────────────────────────────────
/**
 * General-purpose icons used across components.
 * Not semantically grouped — used wherever the action matches the label.
 */
export const UtilityIcons = {
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  Close: X,
  Add: Plus,
  Search,
  Filter,
  More: MoreHorizontal,
  ExternalLink,
  Copy,
  Loading: Loader2,
  Show: Eye,
  Hide: EyeOff,
  ArrowRight,
  Refresh: RefreshCw,
  Delete: Trash2,
  Edit: Pencil,
  ZoomIn,
  ZoomOut,
  Expand: Maximize2,
  ToggleSidebar: PanelLeft,
  Logout: LogOut,
  Menu,
} as const satisfies Record<string, LucideIcon>;

// ─── Composite Export ─────────────────────────────────────────────────────────
/**
 * All icon groups in a single namespace.
 * Prefer importing named groups directly:
 *   import { NavIcons } from '@/config/icons'
 *
 * Use `icons` only when the group is determined dynamically at runtime.
 */
export const icons = {
  nav:        NavIcons,
  memoryType: MemoryTypeIcons,
  entityType: EntityTypeIcons,
  status:     StatusIcons,
  ai:         AIIcons,
  utility:    UtilityIcons,
} as const;

export type Icons = typeof icons;
export type NavIconKey        = keyof typeof NavIcons;
export type MemoryTypeIconKey = keyof typeof MemoryTypeIcons;
export type EntityTypeIconKey = keyof typeof EntityTypeIcons;
export type StatusIconKey     = keyof typeof StatusIcons;
export type AIIconKey         = keyof typeof AIIcons;

export default icons;
