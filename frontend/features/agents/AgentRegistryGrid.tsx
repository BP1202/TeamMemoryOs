/**
 * AgentRegistryGrid — grid of registered agent cards.
 *
 * Renders: loading skeleton, empty state, error state, data grid.
 * Uses React Query for fetching — no direct API calls.
 */

import { useQuery } from '@tanstack/react-query';
import { NavIcons } from '@config/icons';
import { SkeletonCard } from '@components/ui/Skeleton';
import { EmptyState } from '@components/feedback/EmptyState';
import { ErrorState } from '@components/feedback/ErrorState';
import { useAgentStore } from '@stores/agentStore';
import { listAgents } from '@services/agentsService';
import { AgentCard } from './AgentCard';

export const AGENTS_QUERY_KEY = ['agents'] as const;

export function AgentRegistryGrid() {
  const selectedAgentName = useAgentStore((s) => s.selectedAgentName);
  const setSelectedAgent  = useAgentStore((s) => s.setSelectedAgent);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: AGENTS_QUERY_KEY,
    queryFn: ({ signal }) => listAgents(signal),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        aria-busy="true"
        aria-label="Loading agents"
        data-testid="agent-registry-loading"
      >
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        heading="Failed to load agents"
        message="Could not fetch the agent registry. Check your connection and try again."
        onRetry={() => void refetch()}
        data-testid="agent-registry-error"
      />
    );
  }

  const agents = data?.agents ?? [];

  if (agents.length === 0) {
    return (
      <EmptyState
        icon={NavIcons.Agents}
        heading="No agents registered"
        description="No agents are currently registered in this organization."
        data-testid="agent-registry-empty"
      />
    );
  }

  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="agent-registry-grid"
    >
      {agents.map((agent) => (
        <AgentCard
          key={agent.name}
          agent={agent}
          isSelected={selectedAgentName === agent.name}
          onSelect={(name) =>
            setSelectedAgent(selectedAgentName === name ? null : name)
          }
        />
      ))}
    </div>
  );
}
