/**
 * AppShell — root workspace chrome.
 * Composes Sidebar + Topbar + main content area.
 */

import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { cn } from '@utils/cn';

export function AppShell() {
  return (
    <div className="flex h-screen bg-surface-base overflow-hidden">
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar />

        <main
          className={cn(
            'flex-1 overflow-y-auto overflow-x-hidden',
            'bg-surface-base',
          )}
          id="main-content"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
