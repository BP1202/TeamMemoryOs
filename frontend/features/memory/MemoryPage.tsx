/**
 * MemoryPage — organizational memory workspace.
 *
 * Features:
 *   - Paginated, filtered memory entry list.
 *   - Semantic search with 300ms debounce.
 *   - Memory type filter chips.
 *   - Scenario filter list.
 *   - Create Memory drawer.
 *   - Memory Detail drawer with deep-link support.
 *   - Create Scenario dialog.
 *   - Loading, empty, and error states.
 *
 * Rules:
 *   - React Query owns all server state.
 *   - Zustand (memoryStore) owns UI state only.
 *   - No direct API calls in this component.
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@components/ui/Button';
import { Card, CardContent } from '@components/ui/Card';
import { EmptyState } from '@components/feedback/EmptyState';
import { ErrorState } from '@components/feedback/ErrorState';
import { NavIcons, UtilityIcons } from '@config/icons';
import { STALE_TIME_MEMORY, DEFAULT_PAGE_SIZE } from '@config/constants';
import { useAuthStore } from '@stores/authStore';
import { useMemoryStore } from '@stores/memoryStore';
import { listMemoryEntries } from '@services/memoryService';
import { MemoryTable } from './MemoryTable';
import { MemoryTableSkeleton } from './MemoryTableSkeleton';
import { MemorySearchBar } from './MemorySearchBar';
import { MemoryDetailDrawer } from './MemoryDetailDrawer';
import { CreateMemoryDrawer } from './CreateMemoryDrawer';
import { ScenarioList, SCENARIO_LIST_KEY } from './ScenarioList';
import { CreateScenarioDialog } from './CreateScenarioDialog';
import { MEMORY_TYPES, MEMORY_TYPE_LABELS } from '@typedefs/memory';
import { listScenarios } from '@services/scenarioService';
import type { MemoryType } from '@typedefs/memory';

// ─── Query key ─────────────────────────────────────────────────────────────

export const MEMORY_LIST_KEY = (orgId: string) =>
  ['memory', 'list', orgId] as const;

// ─── Component ─────────────────────────────────────────────────────────────

export function MemoryPage() {
  const orgId = useAuthStore((s) => s.user?.id ?? '');

  const filters         = useMemoryStore((s) => s.filters);
  const openCreateDrawer = useMemoryStore((s) => s.openCreateDrawer);
  const setFilter       = useMemoryStore((s) => s.setFilter);
  const resetFilters    = useMemoryStore((s) => s.resetFilters);

  const [isScenarioDialogOpen, setScenarioDialogOpen] = useState(false);

  // ─── Data queries ──────────────────────────────────────────────────────

  const memoriesQ = useQuery({
    queryKey: MEMORY_LIST_KEY(orgId),
    queryFn:  () => listMemoryEntries(orgId, { limit: DEFAULT_PAGE_SIZE * 5 }),
    staleTime: STALE_TIME_MEMORY,
    enabled:  Boolean(orgId),
  });

  const scenariosQ = useQuery({
    queryKey: SCENARIO_LIST_KEY(orgId),
    queryFn:  () => listScenarios(orgId),
    staleTime: STALE_TIME_MEMORY,
    enabled:  Boolean(orgId),
  });

  // ─── Client-side filter + search ───────────────────────────────────────

  const filteredEntries = useMemo(() => {
    const entries = memoriesQ.data ?? [];
    return entries.filter((entry) => {
      // Memory type filter
      if (filters.memoryType !== 'all' && entry.memory_type !== filters.memoryType) {
        return false;
      }
      // Scenario filter
      if (filters.scenarioId !== 'all' && entry.scenario_id !== filters.scenarioId) {
        return false;
      }
      // Text search (client-side against title + content)
      if (filters.search.trim()) {
        const q = filters.search.toLowerCase();
        const inTitle   = entry.title?.toLowerCase().includes(q) ?? false;
        const inContent = entry.content.toLowerCase().includes(q);
        if (!inTitle && !inContent) return false;
      }
      return true;
    });
  }, [memoriesQ.data, filters]);

  const hasActiveFilters =
    filters.memoryType !== 'all' ||
    filters.scenarioId !== 'all' ||
    filters.search.trim() !== '';

  // ─── Render ────────────────────────────────────────────────────────────

  return (
    <div className="p-8 space-y-6" data-testid="memory-page">
      {/* Page header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary flex items-center gap-2">
            <NavIcons.Memory className="h-6 w-6 text-brand" aria-hidden="true" />
            Memory Workspace
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Browse, search, and manage your team's organizational memory.
          </p>
        </div>

        <Button
          onClick={openCreateDrawer}
          aria-label="Create new memory entry"
          data-testid="create-memory-btn"
        >
          <UtilityIcons.Add className="h-4 w-4" aria-hidden="true" />
          New Memory
        </Button>
      </div>

      {/* Scenario filter row */}
      <section aria-labelledby="scenarios-heading">
        <h2
          id="scenarios-heading"
          className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
        >
          Scenarios
        </h2>
        <ScenarioList onCreateScenario={() => setScenarioDialogOpen(true)} />
      </section>

      {/* Search + type filters row */}
      <div className="flex items-center gap-4 flex-wrap">
        <MemorySearchBar />

        {/* Memory type chips */}
        <div
          className="flex items-center gap-2 flex-wrap"
          role="group"
          aria-label="Filter by memory type"
        >
          <button
            onClick={() => setFilter({ memoryType: 'all' })}
            aria-pressed={filters.memoryType === 'all'}
            className="px-3 py-1 rounded-full text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand bg-surface-subtle text-text-secondary hover:bg-surface-elevated data-[state=active]:bg-brand data-[state=active]:text-white"
            style={{
              background: filters.memoryType === 'all' ? 'var(--color-brand)' : undefined,
              color:      filters.memoryType === 'all' ? 'white' : undefined,
            }}
          >
            All types
          </button>
          {MEMORY_TYPES.map((t: MemoryType) => (
            <button
              key={t}
              onClick={() => setFilter({ memoryType: t })}
              aria-pressed={filters.memoryType === t}
              className="px-3 py-1 rounded-full text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand bg-surface-subtle text-text-secondary hover:bg-surface-elevated"
              style={{
                background: filters.memoryType === t ? 'var(--color-brand)' : undefined,
                color:      filters.memoryType === t ? 'white' : undefined,
              }}
            >
              {MEMORY_TYPE_LABELS[t]}
            </button>
          ))}
        </div>

        {/* Active filter indicator + reset */}
        {hasActiveFilters && (
          <button
            onClick={resetFilters}
            className="text-xs text-text-muted hover:text-danger underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded"
            aria-label="Clear all filters"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Entry count */}
      {!memoriesQ.isLoading && !memoriesQ.isError && (
        <p className="text-xs text-text-muted" aria-live="polite">
          {filteredEntries.length === (memoriesQ.data?.length ?? 0)
            ? `${filteredEntries.length} entr${filteredEntries.length === 1 ? 'y' : 'ies'}`
            : `${filteredEntries.length} of ${memoriesQ.data?.length ?? 0} entr${(memoriesQ.data?.length ?? 0) === 1 ? 'y' : 'ies'}`}
        </p>
      )}

      {/* Table */}
      <Card variant="default" className="overflow-hidden p-0">
        <CardContent className="p-0">
          {/* Loading state */}
          {memoriesQ.isLoading && <MemoryTableSkeleton rows={8} />}

          {/* Error state */}
          {memoriesQ.isError && (
            <ErrorState
              heading="Failed to load memories"
              message="Could not retrieve memory entries. Please try again."
              onRetry={() => void memoriesQ.refetch()}
            />
          )}

          {/* Empty state — no data at all */}
          {!memoriesQ.isLoading && !memoriesQ.isError && (memoriesQ.data?.length ?? 0) === 0 && (
            <EmptyState
              icon={NavIcons.Memory}
              heading="No memories yet"
              description="Start capturing decisions, context, and insights for your team."
              action={
                <Button onClick={openCreateDrawer} size="sm">
                  Create your first memory
                </Button>
              }
            />
          )}

          {/* Empty state — filters match nothing */}
          {!memoriesQ.isLoading &&
            !memoriesQ.isError &&
            (memoriesQ.data?.length ?? 0) > 0 &&
            filteredEntries.length === 0 && (
              <EmptyState
                icon={UtilityIcons.Search}
                heading="No matching memories"
                description="Try adjusting your search or filter."
                action={
                  <Button variant="secondary" size="sm" onClick={resetFilters}>
                    Clear filters
                  </Button>
                }
              />
            )}

          {/* Data state */}
          {!memoriesQ.isLoading &&
            !memoriesQ.isError &&
            filteredEntries.length > 0 && (
              <MemoryTable
                entries={filteredEntries}
                scenarios={scenariosQ.data ?? []}
              />
            )}
        </CardContent>
      </Card>

      {/* Drawers + Dialog */}
      <MemoryDetailDrawer />
      <CreateMemoryDrawer />
      <CreateScenarioDialog
        open={isScenarioDialogOpen}
        onOpenChange={setScenarioDialogOpen}
      />
    </div>
  );
}
