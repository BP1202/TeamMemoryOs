/**
 * Navigation configuration.
 * Keys map to NavIcons keys for icon resolution.
 * Used by Sidebar and Topbar components.
 */

import type { NavItem } from '@typedefs/ui';

export const primaryNav: NavItem[] = [
  {
    key: 'Dashboard',
    label: 'Dashboard',
    path: '/',
    icon: 'Dashboard',
  },
  {
    key: 'Memory',
    label: 'Memory',
    path: '/memory',
    icon: 'Memory',
  },
  {
    key: 'Graph',
    label: 'Knowledge Graph',
    path: '/graph',
    icon: 'Graph',
  },
  {
    key: 'Chat',
    label: 'AI Chat',
    path: '/chat',
    icon: 'Chat',
  },
  {
    key: 'Agents',
    label: 'Agents',
    path: '/agents',
    icon: 'Agents',
  },
];

export const bottomNav: NavItem[] = [
  {
    key: 'Settings',
    label: 'Settings',
    path: '/settings',
    icon: 'Settings',
  },
];
