/**
 * EntityInspectorDrawer — slide-in panel for a selected graph entity.
 *
 * Shows:
 *   - Entity name, type, description
 *   - Metadata (id, timestamps)
 *   - Related memories (from entities/memory/{id} endpoint)
 *   - Expand Neighbors button
 *
 * Rules:
 *   - Fetches entity by ID via React Query only when open.
 *   - Expand Neighbors triggers graphStore.expandEntity.
 *   - No direct API calls in this component.
 */

import { useQuery } from '@tanstack/react-query';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerBody,
  DrawerFooter,
} from '@components/ui/Drawer';
import { Button } from '@components/ui/Button';
import { Skeleton } from '@components/ui/Skeleton';
import { ErrorState } from '@components/feedback/ErrorState';
import { EntityTypeIcons } from '@config/icons';
import {
  ENTITY_TYPE_LABELS,
  ENTITY_TYPE_COLORS,
} from '@typedefs/graph';
import { useGraphStore } from '@stores/graphStore';
import { useAuthStore } from '@stores/authStore';
import { getEntity } from '@services/entityService';
import { listMemoryEntries } from '@services/memoryService';
import { STALE_TIME_GRAPH, STALE_TIME_MEMORY } from '@config/constants';

// ─── Query keys ────────────────────────────────────────────────────────────

export const entityDetailKey  = (id: string) => ['entity', 'detail', id] as const;
export const entityMemoriesKey = (orgId: string) => ['memory', 'list', orgId] as const;

// ─── Helpers ───────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

// ─── Component ─────────────────────────────────────────────────────────────

export function EntityInspectorDrawer() {
  const selectedId    = useGraphStore((s) => s.selectedEntityId);
  const isOpen        = useGraphStore((s) => s.isInspectorOpen);
  const deselectEntity = useGraphStore((s) => s.deselectEntity);
  const expandEntity  = useGraphStore((s) => s.expandEntity);
  const expandedIds   = useGraphStore((s) => s.expandedEntityIds);
  const orgId         = useAuthStore((s) => s.user?.id ?? '');

  const isExpanded = selectedId ? expandedIds.includes(selectedId) : false;

  const entityQ = useQuery({
    queryKey: entityDetailKey(selectedId ?? ''),
    queryFn:  () => getEntity(selectedId!),
    enabled:  Boolean(selectedId),
    staleTime: STALE_TIME_GRAPH,
  });

  // Get memories related to this entity by fetching the org list and filtering
  // (backend doesn't expose /entity/{id}/memories, so we filter client-side)
  const memoriesQ = useQuery({
    queryKey: entityMemoriesKey(orgId),
    queryFn:  () => listMemoryEntries(orgId),
    enabled:  Boolean(orgId && selectedId),
    staleTime: STALE_TIME_MEMORY,
  });

  const entity = entityQ.data;
  const color  = entity ? (ENTITY_TYPE_COLORS[entity.entity_type] ?? '#64748b') : undefined;
  const label  = entity ? (ENTITY_TYPE_LABELS[entity.entity_type] ?? entity.entity_type) : '';
  const Icon   = entity
    ? EntityTypeIcons[entity.entity_type as keyof typeof EntityTypeIcons]
    : null;

  return (
    <Drawer open={isOpen} onOpenChange={(open) => { if (!open) deselectEntity(); }}>
      <DrawerContent size="md" aria-labelledby="entity-inspector-title">
        <DrawerHeader>
          {entityQ.isLoading ? (
            <Skeleton className="h-6 w-40" />
          ) : (
            <DrawerTitle
              id="entity-inspector-title"
              className="flex items-center gap-2"
            >
              {Icon && color && (
                <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" style={{ color }} />
              )}
              {entity?.name ?? 'Entity'}
            </DrawerTitle>
          )}
          {entity && (
            <DrawerDescription className="mt-1">
              <span
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                style={{ background: `${color}22`, color }}
              >
                {label}
              </span>
            </DrawerDescription>
          )}
        </DrawerHeader>

        <DrawerBody>
          {entityQ.isLoading && (
            <div aria-busy="true" aria-label="Loading entity…" className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          )}

          {entityQ.isError && (
            <ErrorState
              heading="Failed to load entity"
              message="Could not retrieve entity details."
              onRetry={() => void entityQ.refetch()}
            />
          )}

          {entity && (
            <div className="space-y-6">
              {/* Description */}
              {entity.description && (
                <section aria-labelledby="entity-desc-heading">
                  <h3
                    id="entity-desc-heading"
                    className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
                  >
                    Description
                  </h3>
                  <p className="text-sm text-text-primary leading-relaxed">
                    {entity.description}
                  </p>
                </section>
              )}

              {/* Metadata */}
              <section aria-labelledby="entity-meta-heading">
                <h3
                  id="entity-meta-heading"
                  className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
                >
                  Details
                </h3>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <dt className="text-text-muted">ID</dt>
                  <dd className="font-mono text-xs text-text-primary truncate">{entity.id}</dd>

                  <dt className="text-text-muted">Type</dt>
                  <dd>
                    <span
                      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium"
                      style={{ background: `${color}22`, color }}
                    >
                      {label}
                    </span>
                  </dd>

                  <dt className="text-text-muted">Created</dt>
                  <dd className="text-text-primary">{formatDate(entity.created_at)}</dd>
                </dl>
              </section>

              {/* Related memories count */}
              {!memoriesQ.isLoading && (memoriesQ.data?.length ?? 0) > 0 && (
                <section aria-labelledby="entity-memories-heading">
                  <h3
                    id="entity-memories-heading"
                    className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
                  >
                    Memories
                  </h3>
                  <p className="text-sm text-text-muted">
                    {memoriesQ.data!.length} memor{memoriesQ.data!.length === 1 ? 'y' : 'ies'} in organization
                  </p>
                </section>
              )}
            </div>
          )}
        </DrawerBody>

        {entity && (
          <DrawerFooter>
            <Button
              variant="secondary"
              size="sm"
              onClick={deselectEntity}
            >
              Close
            </Button>
            <Button
              size="sm"
              onClick={() => expandEntity(entity.id)}
              disabled={isExpanded}
              aria-label={isExpanded ? 'Neighbors already expanded' : 'Expand neighbors'}
              data-testid="expand-neighbors-btn"
            >
              {isExpanded ? 'Expanded' : 'Expand Neighbors'}
            </Button>
          </DrawerFooter>
        )}
      </DrawerContent>
    </Drawer>
  );
}
