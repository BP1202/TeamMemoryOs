/**
 * GraphPage — Knowledge Graph Workspace.
 *
 * Features:
 *   - Interactive graph canvas (React Flow)
 *   - Entity type + relationship type filter chips
 *   - Debounced search
 *   - Entity inspector drawer
 *   - Expand neighbors (progressive loading)
 *   - Reset Graph button
 *   - MiniMap, Controls, Background
 *   - Accessible fallback table
 *   - Loading, empty, and error states
 *
 * Architecture:
 *   - React Query owns entities + relationships + neighbor data
 *   - Zustand (graphStore) owns selected entity, expanded nodes, filters
 *   - No direct API calls in this component
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@components/ui/Button';
import { EmptyState } from '@components/feedback/EmptyState';
import { ErrorState } from '@components/feedback/ErrorState';
import { Spinner } from '@components/ui/Spinner';
import { NavIcons, UtilityIcons } from '@config/icons';
import { STALE_TIME_GRAPH } from '@config/constants';
import { useAuthStore } from '@stores/authStore';
import { useGraphStore } from '@stores/graphStore';
import { listEntities } from '@services/entityService';
import { listOutgoingRelationships, listNeighbors } from '@services/relationshipService';
import { GraphCanvas } from './GraphCanvas';
import { GraphSearchBar } from './GraphSearchBar';
import { EntityInspectorDrawer } from './EntityInspectorDrawer';
import { GraphFallbackTable } from './GraphFallbackTable';
import {
  ENTITY_TYPES,
  ENTITY_TYPE_LABELS,
  ENTITY_TYPE_COLORS,
  RELATIONSHIP_TYPES,
  RELATIONSHIP_TYPE_LABELS,
} from '@typedefs/graph';
import type { EntityType, RelationshipType, Entity, Relationship } from '@typedefs/graph';

// ─── Query keys ────────────────────────────────────────────────────────────

export const ENTITY_LIST_KEY  = (orgId: string) => ['entities', 'list', orgId] as const;
export const REL_LIST_KEY     = (entityId: string) => ['relationships', 'outgoing', entityId] as const;
export const NEIGHBOR_KEY     = (entityId: string, orgId: string) =>
  ['relationships', 'neighbors', entityId, orgId] as const;

// ─── Neighbor expansion hook ───────────────────────────────────────────────

function useNeighborEntities(
  expandedIds: string[],
  orgId: string,
): { neighborEntities: Entity[]; neighborRelationships: Relationship[] } {
  // We fetch neighbors for the first expanded entity (could be extended to all)
  const firstExpandedId = expandedIds[0] ?? null;

  const neighborQ = useQuery({
    queryKey: NEIGHBOR_KEY(firstExpandedId ?? '', orgId),
    queryFn:  () => listNeighbors(firstExpandedId!, orgId),
    enabled:  Boolean(firstExpandedId && orgId),
    staleTime: STALE_TIME_GRAPH,
  });

  const neighborEntities: Entity[] = useMemo(
    () => neighborQ.data?.map((n) => n.entity) ?? [],
    [neighborQ.data],
  );

  const neighborRelationships: Relationship[] = useMemo(
    () => neighborQ.data?.map((n) => ({
      id:                n.relationship_id,
      organization_id:   orgId,
      source_entity_id:  n.direction === 'outgoing' ? firstExpandedId! : n.entity.id,
      target_entity_id:  n.direction === 'outgoing' ? n.entity.id : firstExpandedId!,
      relationship_type: n.relationship_type,
      created_at:        '',
    })) ?? [],
    [neighborQ.data, firstExpandedId, orgId],
  );

  return { neighborEntities, neighborRelationships };
}

// ─── Component ─────────────────────────────────────────────────────────────

export function GraphPage() {
  const orgId = useAuthStore((s) => s.user?.id ?? '');

  const filters         = useGraphStore((s) => s.filters);
  const expandedIds     = useGraphStore((s) => s.expandedEntityIds);
  const selectEntity    = useGraphStore((s) => s.selectEntity);
  const setFilter       = useGraphStore((s) => s.setFilter);
  const resetGraph      = useGraphStore((s) => s.resetGraph);
  const resetFilters    = useGraphStore((s) => s.resetFilters);

  // ── Entity list ────────────────────────────────────────────────────────

  const entitiesQ = useQuery({
    queryKey: ENTITY_LIST_KEY(orgId),
    queryFn:  () => listEntities(orgId, { limit: 200 }),
    staleTime: STALE_TIME_GRAPH,
    enabled:  Boolean(orgId),
  });

  // ── Relationships — fetch outgoing for each visible entity ─────────────
  // Simplified: fetch outgoing for first 10 entities (progressive)
  const firstEntity = entitiesQ.data?.[0];
  const relsQ = useQuery({
    queryKey: REL_LIST_KEY(firstEntity?.id ?? ''),
    queryFn:  () => listOutgoingRelationships(firstEntity!.id, { limit: 500 }),
    staleTime: STALE_TIME_GRAPH,
    enabled:  Boolean(firstEntity?.id),
  });

  // ── Neighbor expansion ─────────────────────────────────────────────────

  const { neighborEntities, neighborRelationships } = useNeighborEntities(expandedIds, orgId);

  // ── Merge entities and relationships ──────────────────────────────────

  const allEntities: Entity[] = useMemo(() => {
    const base  = entitiesQ.data ?? [];
    const known = new Set(base.map((e) => e.id));
    const extra = neighborEntities.filter((e) => !known.has(e.id));
    return [...base, ...extra];
  }, [entitiesQ.data, neighborEntities]);

  const allRelationships: Relationship[] = useMemo(() => {
    const base  = relsQ.data ?? [];
    const known = new Set(base.map((r) => r.id));
    const extra = neighborRelationships.filter((r) => !known.has(r.id));
    return [...base, ...extra];
  }, [relsQ.data, neighborRelationships]);

  // ── Client-side filter for fallback table ─────────────────────────────
  // Also computed here so fallback table stays in sync with canvas filters.

  const filteredForTable: Entity[] = useMemo(() => {
    return allEntities.filter((e) => {
      if (filters.entityType !== 'all' && e.entity_type !== filters.entityType) return false;
      if (filters.search.trim()) {
        const q = filters.search.toLowerCase();
        if (!e.name.toLowerCase().includes(q) &&
            !(e.description?.toLowerCase().includes(q) ?? false)) return false;
      }
      return true;
    });
  }, [allEntities, filters.entityType, filters.search]);

  const hasActiveFilters =
    filters.entityType !== 'all' ||
    filters.relationshipType !== 'all' ||
    filters.search.trim() !== '';

  const isLoading = entitiesQ.isLoading;
  const isError   = entitiesQ.isError;
  const isEmpty   = !isLoading && !isError && allEntities.length === 0;

  // ─── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-[calc(100vh-56px)] overflow-hidden" data-testid="graph-page">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-border bg-surface flex-shrink-0 flex-wrap">
        <div className="flex items-center gap-2">
          <NavIcons.Graph className="h-5 w-5 text-brand" aria-hidden="true" />
          <h1 className="text-base font-semibold text-text-primary">Knowledge Graph</h1>
        </div>

        <div className="flex-1" />

        <GraphSearchBar />

        {/* Entity type filter */}
        <div
          className="flex items-center gap-1.5 flex-wrap"
          role="group"
          aria-label="Filter by entity type"
        >
          <button
            onClick={() => setFilter({ entityType: 'all' })}
            aria-pressed={filters.entityType === 'all'}
            className="px-2.5 py-1 rounded-full text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            style={{
              background: filters.entityType === 'all' ? 'var(--color-brand)' : 'var(--color-surface-subtle)',
              color:      filters.entityType === 'all' ? 'white' : 'var(--color-text-secondary)',
            }}
          >
            All
          </button>
          {ENTITY_TYPES.map((t: EntityType) => (
            <button
              key={t}
              onClick={() => setFilter({ entityType: t })}
              aria-pressed={filters.entityType === t}
              className="px-2.5 py-1 rounded-full text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              style={{
                background: filters.entityType === t ? ENTITY_TYPE_COLORS[t] : 'var(--color-surface-subtle)',
                color:      filters.entityType === t ? 'white' : 'var(--color-text-secondary)',
              }}
            >
              {ENTITY_TYPE_LABELS[t]}
            </button>
          ))}
        </div>

        {/* Relationship type filter */}
        <select
          value={filters.relationshipType}
          onChange={(e) => setFilter({ relationshipType: e.target.value as RelationshipType | 'all' })}
          className="text-xs rounded-md bg-surface-subtle text-text-secondary border border-border px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand"
          aria-label="Filter by relationship type"
        >
          <option value="all">All relationships</option>
          {RELATIONSHIP_TYPES.map((t) => (
            <option key={t} value={t}>{RELATIONSHIP_TYPE_LABELS[t]}</option>
          ))}
        </select>

        {/* Reset button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={resetGraph}
          aria-label="Reset graph view"
          data-testid="reset-graph-btn"
        >
          <UtilityIcons.Refresh className="h-3.5 w-3.5" aria-hidden="true" />
          Reset
        </Button>

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

      {/* Canvas area */}
      <div className="flex-1 relative overflow-hidden bg-surface-base">
        {/* Loading */}
        {isLoading && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            aria-busy="true"
            aria-label="Loading knowledge graph…"
            data-testid="graph-loading"
          >
            <Spinner size="lg" label="Loading knowledge graph…" />
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <ErrorState
              heading="Failed to load graph"
              message="Could not retrieve entities. Please try again."
              onRetry={() => void entitiesQ.refetch()}
            />
          </div>
        )}

        {/* Empty */}
        {isEmpty && (
          <div className="absolute inset-0 flex items-center justify-center">
            <EmptyState
              icon={NavIcons.Graph}
              heading="No entities yet"
              description="The knowledge graph will populate as memory entries are created."
            />
          </div>
        )}

        {/* Graph canvas */}
        {!isLoading && !isError && !isEmpty && (
          <GraphCanvas
            entities={allEntities}
            relationships={allRelationships}
          />
        )}
      </div>

      {/* Accessible fallback table — always visible below canvas */}
      {!isLoading && !isError && allEntities.length > 0 && (
        <div
          className="px-6 pb-8 overflow-y-auto border-t border-border bg-surface"
          style={{ maxHeight: '40vh' }}
        >
          <GraphFallbackTable
            entities={filteredForTable}
            relationships={allRelationships}
            onSelectEntity={selectEntity}
          />
        </div>
      )}

      {/* Entity inspector drawer */}
      <EntityInspectorDrawer />
    </div>
  );
}
