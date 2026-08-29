/**
 * DashboardPage — main workspace landing.
 *
 * Sprint 8.0: Placeholder shell confirming routing + AppShell work.
 * Sprint 8.1 will populate with real widgets and API data.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { APP_NAME } from '@config/constants';

export function DashboardPage() {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">
          Welcome to {APP_NAME}
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Your AI Operating System for Engineering Teams.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Memory</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-secondary">
              Organizational memory workspace (Sprint 8.2)
            </p>
          </CardContent>
        </Card>

        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Knowledge Graph</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-secondary">
              Entity relationship visualizer (Sprint 8.3)
            </p>
          </CardContent>
        </Card>

        <Card variant="elevated">
          <CardHeader>
            <CardTitle>AI Chat</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-secondary">
              Granite-powered AI assistant (Sprint 8.4)
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
