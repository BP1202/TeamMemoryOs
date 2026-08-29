/**
 * Sidebar — workspace navigation panel.
 *
 * Rules:
 *   - Reads sidebarCollapsed from UI store.
 *   - Icons come from NavIcons registry only.
 *   - No API calls.
 *   - Keyboard navigable: all links focusable.
 */

import { NavLink } from 'react-router-dom';
import { m, useReducedMotion } from 'framer-motion';
import { NavIcons, UtilityIcons, iconSize } from '@config/icons';
import { primaryNav, bottomNav } from '@config/navigation';
import { useUIStore } from '@stores/uiStore';
import { useAuthStore } from '@stores/authStore';
import { APP_NAME } from '@config/constants';
import { cn } from '@utils/cn';
import type { NavItem } from '@typedefs/ui';

// ─── Icon resolver ─────────────────────────────────────────────────────────

function NavIcon({ iconKey }: { iconKey: string }) {
  const Icon = NavIcons[iconKey as keyof typeof NavIcons];
  return Icon
    ? <Icon className={iconSize.nav} aria-hidden="true" />
    : null;
}

// ─── Nav item ──────────────────────────────────────────────────────────────

interface NavItemProps {
  item: NavItem;
  collapsed: boolean;
}

function SidebarNavItem({ item, collapsed }: NavItemProps) {
  return (
    <NavLink
      to={item.path}
      end={item.path === '/'}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-md',
          'text-sm font-medium transition-colors duration-fast',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
          isActive
            ? 'bg-brand-subtle text-brand hover:bg-brand-subtle'
            : 'text-text-secondary hover:text-text-primary hover:bg-surface-subtle',
          collapsed && 'justify-center px-2',
        )
      }
      title={collapsed ? item.label : undefined}
      aria-label={collapsed ? item.label : undefined}
    >
      <NavIcon iconKey={item.icon} />
      {!collapsed && <span>{item.label}</span>}
      {!collapsed && item.badge != null && (
        <span className="ml-auto text-xs font-medium bg-brand text-white px-1.5 py-0.5 rounded-full">
          {item.badge}
        </span>
      )}
    </NavLink>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────

export function Sidebar() {
  const collapsed   = useUIStore((s) => s.sidebarCollapsed);
  const toggle      = useUIStore((s) => s.toggleSidebar);
  const user        = useAuthStore((s) => s.user);
  const clearAuth   = useAuthStore((s) => s.clearAuth);
  const prefersReduced = useReducedMotion();

  const width = collapsed ? 64 : 240;

  return (
    <m.nav
      initial={false}
      animate={{ width }}
      transition={prefersReduced ? { duration: 0 } : { duration: 0.2, ease: 'easeInOut' }}
      className={cn(
        'flex flex-col h-screen',
        'bg-surface border-r border-border',
        'z-sidebar flex-shrink-0 overflow-hidden',
      )}
      aria-label="Main navigation"
    >
      {/* Logo + toggle */}
      <div className={cn(
        'flex items-center h-topbar border-b border-border px-3 flex-shrink-0',
        collapsed ? 'justify-center' : 'justify-between',
      )}>
        {!collapsed && (
          <span className="text-sm font-semibold text-text-primary truncate">
            {APP_NAME}
          </span>
        )}
        <button
          onClick={toggle}
          className={cn(
            'rounded-md p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-subtle',
            'transition-colors duration-fast',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <UtilityIcons.ToggleSidebar className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {/* Primary navigation */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 space-y-1">
        {primaryNav.map((item) => (
          <SidebarNavItem key={item.key} item={item} collapsed={collapsed} />
        ))}
      </div>

      {/* Bottom: settings + user */}
      <div className="py-3 px-2 space-y-1 border-t border-border">
        {bottomNav.map((item) => (
          <SidebarNavItem key={item.key} item={item} collapsed={collapsed} />
        ))}

        {user && (
          <button
            onClick={clearAuth}
            className={cn(
              'flex items-center gap-3 w-full px-3 py-2 rounded-md',
              'text-sm font-medium text-text-muted hover:text-danger hover:bg-surface-subtle',
              'transition-colors duration-fast',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
              collapsed && 'justify-center px-2',
            )}
            aria-label="Sign out"
          >
            <UtilityIcons.Logout className={iconSize.nav} aria-hidden="true" />
            {!collapsed && <span>Sign out</span>}
          </button>
        )}
      </div>
    </m.nav>
  );
}
