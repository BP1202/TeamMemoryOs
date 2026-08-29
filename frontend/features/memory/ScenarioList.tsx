/**
 * ScenarioList — displays organization scenarios as filter chips.
 *
 * Clicking a chip sets scenarioId filter in memoryStore.
 * Includes loading, empty, and error states.
 */

import { useQuery } from '@tanstack/react-query';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton } from '@components/ui/Skeleton';
import { useMemoryStore } from '@stores/memoryStore';
import { useAuthStore } from '@stores/authStore';
import { listScenarios } from '@services/scenarioService';
import { STALE_TIME_MEMORY } from '@config/constants';
import { cn } from '@utils/cn';
import type { Scenario } from '@typedefs/memory';

// ─── Query key ─────────────────────────────────────────────────────────────

export const SCENARIO_LIST_KEY = (orgId: string) =>
  ['scenarios', 'list', orgId] as const;

// ─── Props ─────────────────────────────────────────────────────────────────

interface ScenarioListProps {
  onCreateScenario: () => void;
}

// ─── Component ─────────────────────────────────────────────────────────────

export function ScenarioList({ onCreateScenario }: ScenarioListProps) {
  const orgId      = useAuthStore((s) => s.user?.id ?? '');
  const activeId   = useMemoryStore((s) => s.filters.scenarioId);
  const setFilter  = useMemoryStore((s) => s.setFilter);

  const { data: scenarios, isLoading, isError, refetch } = useQuery({
    queryKey: SCENARIO_LIST_KEY(orgId),
    queryFn:  () => listScenarios(orgId),
    staleTime: STALE_TIME_MEMORY,
    enabled:  Boolean(orgId),
  });

  const handleSelect = (scenario: Scenario) => {
    setFilter({ scenarioId: activeId === scenario.id ? 'all' : scenario.id });
  };

  if (isLoading) {
    return (
      <div
        aria-busy="true"
        aria-label="Loading scenarios…"
        className="flex items-center gap-2 flex-wrap"
      >
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-6 w-20 rounded-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div role="alert" className="text-xs text-danger flex items-center gap-2">
        <span>Failed to load scenarios.</span>
        <button
          onClick={() => void refetch()}
          className="underline text-xs text-brand hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 flex-wrap" aria-label="Scenario filters">
      {/* All chip */}
      <button
        onClick={() => setFilter({ scenarioId: 'all' })}
        aria-pressed={activeId === 'all'}
        className={cn(
          'px-3 py-1 rounded-full text-xs font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
          activeId === 'all'
            ? 'bg-brand text-white'
            : 'bg-surface-subtle text-text-secondary hover:bg-surface-elevated hover:text-text-primary',
        )}
      >
        All
      </button>

      {scenarios?.map((scenario) => (
        <button
          key={scenario.id}
          onClick={() => handleSelect(scenario)}
          aria-pressed={activeId === scenario.id}
          className={cn(
            'px-3 py-1 rounded-full text-xs font-medium transition-colors',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
            activeId === scenario.id
              ? 'bg-brand text-white'
              : 'bg-surface-subtle text-text-secondary hover:bg-surface-elevated hover:text-text-primary',
          )}
        >
          {scenario.name}
          {!scenario.is_active && (
            <Badge variant="warning" className="ml-1 text-xs">
              Inactive
            </Badge>
          )}
        </button>
      ))}

      {(!scenarios || scenarios.length === 0) && (
        <span className="text-xs text-text-muted">No scenarios yet.</span>
      )}

      {/* Create button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onCreateScenario}
        aria-label="Create new scenario"
        className="text-xs"
      >
        + New Scenario
      </Button>
    </div>
  );
}
