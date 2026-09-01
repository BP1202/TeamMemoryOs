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
import { useLogout } from '@hooks/useLogout';
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
  const collapsed          = useUIStore((s) => s.sidebarCollapsed);
  const toggle             = useUIStore((s) => s.toggleSidebar);
  const currentWorkspace   = useUIStore((s) => s.currentWorkspace);
  const user               = useAuthStore((s) => s.user);
  const logout             = useLogout();
  const prefersReduced     = useReducedMotion();

  const width = collapsed ? 64 : 256;

  return (
    <m.nav
      initial={false}
      animate={{ width }}
      transition={prefersReduced ? { duration: 0 } : { duration: 0.2, ease: 'easeInOut' }}
      className={cn(
        'flex flex-col h-screen',
        'bg-[#120F24] border-r border-[#2A2447] shadow-2xl',
        'z-sidebar flex-shrink-0 overflow-hidden select-none',
      )}
      aria-label="Main navigation"
    >
      {/* Workspace Header + Toggle */}
      <div className={cn(
        'flex items-center h-16 border-b border-[#2A2447] px-3.5 flex-shrink-0 bg-[#16122C]',
        collapsed ? 'justify-center' : 'justify-between',
      )}>
        {!collapsed ? (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-purple-500 via-indigo-500 to-purple-700 flex items-center justify-center shadow-lg shadow-purple-500/25 text-white font-bold text-sm flex-shrink-0">
              TM
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="text-sm font-semibold text-white tracking-tight truncate">
                {currentWorkspace}
              </span>
              <span className="text-[10px] text-[#A5A0C8] tracking-wider uppercase font-mono">
                AI Engineering Workspace
              </span>
            </div>
          </div>
        ) : (
          <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            TM
          </div>
        )}
        <button
          onClick={toggle}
          className={cn(
            'rounded-md p-1.5 text-[#A5A0C8] hover:text-white hover:bg-white/10',
            'transition-colors duration-fast',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500',
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

      {/* Authenticated User Profile Card */}
      {!collapsed && (
        <div className="p-3 mx-2 mb-2 bg-[#1B1633] border border-[#2D264E] rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {user?.full_name ? user.full_name.slice(0, 2).toUpperCase() : 'DT'}
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="text-xs font-bold text-white truncate">
                {user?.full_name || 'Devin Thorne'}
              </span>
              <span className="text-[10px] text-[#A5A0C8] font-mono truncate">
                {user?.email || 'admin@teammemory.com'}
              </span>
            </div>
          </div>
          <span className="text-[9px] font-mono bg-[#8B5CF6]/20 text-[#C4B5FD] border border-[#8B5CF6]/30 px-2 py-0.5 rounded-full font-bold">
            Active
          </span>
        </div>
      )}

      {/* Bottom: settings + user */}
      <div className="py-2.5 px-2 space-y-1 border-t border-[#2A2447]">
        {bottomNav.map((item) => (
          <SidebarNavItem key={item.key} item={item} collapsed={collapsed} />
        ))}

        {user && (
          <button
            onClick={logout}
            className={cn(
              'flex items-center gap-3 w-full px-3 py-2 rounded-md',
              'text-sm font-medium text-[#A5A0C8] hover:text-rose-400 hover:bg-rose-500/10',
              'transition-colors duration-fast',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500',
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

