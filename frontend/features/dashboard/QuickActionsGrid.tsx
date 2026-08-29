/**
 * QuickActionsGrid — navigation cards to main workspace sections.
 * Leads user into the four core workspace areas.
 */

import { Link } from 'react-router-dom';
import { NavIcons, iconSize } from '@config/icons';
import { Card, CardContent } from '@components/ui/Card';
import { UtilityIcons } from '@config/icons';

interface QuickAction {
  key: string;
  label: string;
  description: string;
  path: string;
  icon: keyof typeof NavIcons;
  available: boolean;
}

const quickActions: QuickAction[] = [
  {
    key: 'memory',
    label: 'Memory',
    description: 'Browse and search organizational memories',
    path: '/memory',
    icon: 'Memory',
    available: false,
  },
  {
    key: 'graph',
    label: 'Knowledge Graph',
    description: 'Explore entity relationships',
    path: '/graph',
    icon: 'Graph',
    available: false,
  },
  {
    key: 'chat',
    label: 'AI Chat',
    description: 'Ask questions with Granite-powered retrieval',
    path: '/chat',
    icon: 'Chat',
    available: false,
  },
  {
    key: 'agents',
    label: 'Agents',
    description: 'Run multi-agent workflows',
    path: '/agents',
    icon: 'Agents',
    available: false,
  },
];

export function QuickActionsGrid() {
  return (
    <div>
      <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">
        Workspaces
      </h2>
      <div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
        role="list"
        aria-label="Quick actions"
      >
        {quickActions.map((action) => {
          const Icon = NavIcons[action.icon];

          return (
            <div role="listitem" key={action.key}>
              {action.available ? (
                <Link
                  to={action.path}
                  className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded-lg"
                >
                  <Card variant="outline" className="h-full cursor-pointer">
                    <CardContent>
                      <div className="flex items-center gap-3 mb-2">
                        <Icon className={iconSize.heading} aria-hidden="true" />
                        <span className="text-sm font-semibold text-text-primary">
                          {action.label}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary">{action.description}</p>
                    </CardContent>
                  </Card>
                </Link>
              ) : (
                <Card
                  variant="outline"
                  className="h-full opacity-60 cursor-not-allowed"
                  aria-label={`${action.label} — coming soon`}
                >
                  <CardContent>
                    <div className="flex items-center gap-3 mb-2">
                      <Icon className={iconSize.heading} aria-hidden="true" />
                      <span className="text-sm font-semibold text-text-primary">
                        {action.label}
                      </span>
                      <UtilityIcons.ArrowRight
                        className="h-3 w-3 text-text-muted ml-auto"
                        aria-hidden="true"
                      />
                    </div>
                    <p className="text-xs text-text-secondary">{action.description}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
