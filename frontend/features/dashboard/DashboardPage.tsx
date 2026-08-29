/**
 * DashboardPage — main AI Workspace dashboard.
 *
 * Displays:
 *   - System health (backend + db)
 *   - Memory, Scenario, Agent counts
 *   - Quick Actions navigation cards
 *
 * All data from React Query — no direct API calls in this component.
 */

import { useQuery } from '@tanstack/react-query';
import { NavIcons } from '@config/icons';
import { APP_NAME } from '@config/constants';
import { useAuthStore } from '@stores/authStore';
import { getMemoryList, getScenarioList, getAgentList } from '@services/dashboardService';
import { HealthWidget } from './HealthWidget';
import { StatWidget } from './StatWidget';
import { QuickActionsGrid } from './QuickActionsGrid';

// ─── Query keys ────────────────────────────────────────────────────────────

export const MEMORY_COUNT_KEY   = ['dashboard', 'memoryCount']   as const;
export const SCENARIO_COUNT_KEY = ['dashboard', 'scenarioCount'] as const;
export const AGENT_COUNT_KEY    = ['dashboard', 'agentCount']    as const;

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  // Stats — memory
  const memoryQ = useQuery({
    queryKey: MEMORY_COUNT_KEY,
    queryFn:  () => getMemoryList('default'),
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });

  // Stats — scenarios
  const scenarioQ = useQuery({
    queryKey: SCENARIO_COUNT_KEY,
    queryFn:  () => getScenarioList('default'),
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });

  // Stats — agents (bounded list, no org_id needed)
  const agentsQ = useQuery({
    queryKey: AGENT_COUNT_KEY,
    queryFn:  getAgentList,
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });

  const greeting = user ? `Welcome back, ${user.full_name.split(' ')[0]}` : `Welcome to ${APP_NAME}`;

  return (
    <div className="p-8 space-y-8" data-testid="dashboard-page">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">{greeting}</h1>
        <p className="text-sm text-text-secondary mt-1">
          Your AI Operating System for Engineering Teams
        </p>
      </div>

      {/* Stats row */}
      <div>
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">
          Overview
        </h2>
        <div
          className="grid grid-cols-1 sm:grid-cols-3 gap-4"
          data-testid="stats-grid"
        >
          <StatWidget
            label="Memories"
            value={memoryQ.data?.length}
            icon={NavIcons.Memory}
            isLoading={memoryQ.isLoading}
            isError={memoryQ.isError}
          />
          <StatWidget
            label="Scenarios"
            value={scenarioQ.data?.length}
            icon={NavIcons.Dashboard}
            isLoading={scenarioQ.isLoading}
            isError={scenarioQ.isError}
          />
          <StatWidget
            label="Agents"
            value={agentsQ.data?.total ?? agentsQ.data?.agents?.length}
            icon={NavIcons.Agents}
            isLoading={agentsQ.isLoading}
            isError={agentsQ.isError}
          />
        </div>
      </div>

      {/* Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <HealthWidget />
      </div>

      {/* Quick Actions */}
      <QuickActionsGrid />
    </div>
  );
}
