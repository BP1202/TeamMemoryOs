/**
 * SettingsPage — application settings scaffold.
 *
 * Sprint 8.6: provides theme toggle, sidebar preference, and system information.
 * Full settings implementation is a future sprint scope.
 */

import { NavIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { useUIStore } from '@stores/uiStore';
import { useAuthStore } from '@stores/authStore';
import { APP_NAME } from '@config/constants';
import type { Theme } from '@typedefs/ui';

const THEMES: Array<{ value: Theme; label: string }> = [
  { value: 'light', label: 'Light' },
  { value: 'dark',  label: 'Dark' },
  { value: 'system', label: 'System' },
];

export function SettingsPage() {
  const theme    = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const user     = useAuthStore((s) => s.user);

  return (
    <div className="px-6 py-6 max-w-2xl mx-auto space-y-6" data-testid="settings-page">

      {/* Page header */}
      <header className="flex items-center gap-3 pb-2 border-b border-border">
        <div className="w-9 h-9 rounded-lg bg-surface-elevated flex items-center justify-center">
          <NavIcons.Settings className="h-5 w-5 text-text-secondary" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-base font-semibold text-text-primary">Settings</h1>
          <p className="text-xs text-text-secondary">
            Manage your workspace preferences.
          </p>
        </div>
      </header>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose your preferred color theme.</CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex gap-2 flex-wrap"
            role="group"
            aria-label="Theme selection"
          >
            {THEMES.map(({ value, label }) => (
              <Button
                key={value}
                variant={theme === value ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setTheme(value)}
                aria-pressed={theme === value}
                aria-label={`Set theme to ${label}`}
              >
                {label}
              </Button>
            ))}
          </div>
          <p className="text-xs text-text-muted mt-2">
            Theme preference is persisted to localStorage.
          </p>
        </CardContent>
      </Card>

      {/* Account */}
      {user && (
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>Your profile information.</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex items-center gap-3">
                <dt className="text-text-secondary w-24 flex-shrink-0">Name</dt>
                <dd className="text-text-primary font-medium">{user.full_name}</dd>
              </div>
              <div className="flex items-center gap-3">
                <dt className="text-text-secondary w-24 flex-shrink-0">Email</dt>
                <dd className="text-text-primary">{user.email}</dd>
              </div>
              <div className="flex items-center gap-3">
                <dt className="text-text-secondary w-24 flex-shrink-0">Status</dt>
                <dd>
                  <Badge variant={user.is_active ? 'success' : 'danger'}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}

      {/* System info */}
      <Card>
        <CardHeader>
          <CardTitle>System</CardTitle>
          <CardDescription>Application version information.</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <dt className="text-text-secondary w-24 flex-shrink-0">App</dt>
              <dd className="text-text-primary">{APP_NAME}</dd>
            </div>
            <div className="flex items-center gap-3">
              <dt className="text-text-secondary w-24 flex-shrink-0">Version</dt>
              <dd className="text-text-primary font-mono">0.1.0</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
