/**
 * Topbar — workspace top navigation bar.
 *
 * Shows current page title, user info, and global actions.
 * Height: var(--topbar-height) = 56px
 */

import { useAuthStore } from '@stores/authStore';
import { cn } from '@utils/cn';

interface TopbarProps {
  title?: string;
}

export function Topbar({ title }: TopbarProps) {
  const user = useAuthStore((s) => s.user);

  return (
    <header
      className={cn(
        'flex items-center justify-between',
        'h-topbar px-6',
        'bg-surface border-b border-border',
        'z-topbar flex-shrink-0',
      )}
      role="banner"
    >
      {/* Page title */}
      <div className="flex items-center gap-3">
        {title && (
          <h1 className="text-sm font-semibold text-text-primary">{title}</h1>
        )}
      </div>

      {/* User info */}
      {user && (
        <div className="flex items-center gap-2" aria-label="Current user">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-medium text-text-primary leading-none">
              {user.full_name}
            </p>
            <p className="text-xs text-text-muted mt-0.5">{user.email}</p>
          </div>
          <div
            className={cn(
              'h-8 w-8 rounded-full flex items-center justify-center',
              'bg-brand-muted text-brand text-xs font-semibold',
            )}
            aria-hidden="true"
          >
            {user.full_name.charAt(0).toUpperCase()}
          </div>
        </div>
      )}
    </header>
  );
}
