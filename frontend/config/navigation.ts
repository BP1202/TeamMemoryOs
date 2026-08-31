/**
 * Navigation configuration for TeamMemoryOS.
 * 5 Pages: Memory Home, AI Assistant, Memory Book, Daily Quests (Arena), Workspace.
 */

import type { NavItem } from '@typedefs/ui';

export const primaryNav: NavItem[] = [
  {
    key: 'Dashboard',
    label: 'Memory Home',
    path: '/',
    icon: 'Dashboard',
  },
  {
    key: 'Chat',
    label: 'AI Assistant',
    path: '/chat',
    icon: 'Chat',
  },
  {
    key: 'Knowledge',
    label: 'Memory Book',
    path: '/knowledge',
    icon: 'Knowledge',
  },
  {
    key: 'Incidents',
    label: 'Daily Quests',
    path: '/incidents',
    icon: 'Incidents',
  },
];

export const bottomNav: NavItem[] = [
  {
    key: 'Workspace',
    label: 'Workspace',
    path: '/workspace',
    icon: 'Workspace',
  },
];
