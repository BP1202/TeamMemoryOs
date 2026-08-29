/**
 * MemoryDetailDrawer — slide-in panel showing full memory entry detail.
 *
 * Supports deep-link via route param /memory/:memoryId.
 * Opens when memoryStore.isDetailDrawerOpen === true.
 *
 * Rules:
 *   - Fetches entry by ID via React Query.
 *   - Loading, error, and data states all present.
 *   - Focus trap and ESC close from Drawer primitive.
 */

import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerBody,
} from '@components/ui/Drawer';
import { Skeleton } from '@components/ui/Skeleton';
import { ErrorState } from '@components/feedback/ErrorState';
import { MemoryTypeBadge } from './MemoryTypeBadge';
import { useMemoryStore } from '@stores/memoryStore';
import { getMemoryEntry } from '@services/memoryService';
import { STALE_TIME_MEMORY } from '@config/constants';

// ─── Query key ─────────────────────────────────────────────────────────────

export const memoryDetailKey = (id: string) => ['memory', 'detail', id] as const;

// ─── Detail content ────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year:   'numeric',
    month:  'short',
    day:    'numeric',
    hour:   '2-digit',
    minute: '2-digit',
  });
}

// ─── Component ─────────────────────────────────────────────────────────────

export function MemoryDetailDrawer() {
  const navigate     = useNavigate();
  const { memoryId: routeMemoryId } = useParams<{ memoryId: string }>();

  const isOpen          = useMemoryStore((s) => s.isDetailDrawerOpen);
  const selectedId      = useMemoryStore((s) => s.selectedMemoryId);
  const closeDrawer     = useMemoryStore((s) => s.closeDetailDrawer);

  // Support both: drawer opened programmatically (selectedId) or via route param
  const memoryId = selectedId ?? routeMemoryId ?? null;

  const { data: entry, isLoading, isError, refetch } = useQuery({
    queryKey: memoryDetailKey(memoryId ?? ''),
    queryFn:  () => getMemoryEntry(memoryId!),
    enabled:  Boolean(memoryId),
    staleTime: STALE_TIME_MEMORY,
  });

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      closeDrawer();
      // Navigate back to /memory on close if we came in via direct URL
      if (routeMemoryId) {
        navigate('/memory', { replace: true });
      }
    }
  };

  const open = isOpen || Boolean(routeMemoryId);

  return (
    <Drawer open={open} onOpenChange={handleOpenChange}>
      <DrawerContent size="md" aria-labelledby="memory-detail-title">
        <DrawerHeader>
          {isLoading ? (
            <Skeleton className="h-6 w-48" />
          ) : (
            <DrawerTitle id="memory-detail-title">
              {entry?.title ?? '(untitled)'}
            </DrawerTitle>
          )}
          {entry && (
            <DrawerDescription className="flex items-center gap-2 mt-1">
              <MemoryTypeBadge type={entry.memory_type} />
              <span className="text-xs text-text-muted">
                Created {formatDate(entry.created_at)}
              </span>
            </DrawerDescription>
          )}
        </DrawerHeader>

        <DrawerBody>
          {isLoading && (
            <div aria-busy="true" aria-label="Loading memory entry…" className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/5" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          )}

          {isError && (
            <ErrorState
              heading="Failed to load memory entry"
              message="The entry could not be retrieved. Please try again."
              onRetry={() => void refetch()}
            />
          )}

          {entry && (
            <div className="space-y-6">
              {/* Content */}
              <section aria-labelledby="memory-content-heading">
                <h3
                  id="memory-content-heading"
                  className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
                >
                  Content
                </h3>
                {/* Plain text — never innerHTML */}
                <p className="text-sm text-text-primary whitespace-pre-wrap leading-relaxed">
                  {entry.content}
                </p>
              </section>

              {/* Metadata */}
              <section aria-labelledby="memory-meta-heading">
                <h3
                  id="memory-meta-heading"
                  className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
                >
                  Metadata
                </h3>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <dt className="text-text-muted">ID</dt>
                  <dd className="text-text-primary font-mono text-xs truncate">{entry.id}</dd>

                  <dt className="text-text-muted">Type</dt>
                  <dd><MemoryTypeBadge type={entry.memory_type} /></dd>

                  <dt className="text-text-muted">Created</dt>
                  <dd className="text-text-primary">{formatDate(entry.created_at)}</dd>

                  <dt className="text-text-muted">Updated</dt>
                  <dd className="text-text-primary">{formatDate(entry.updated_at)}</dd>

                  {entry.scenario_id && (
                    <>
                      <dt className="text-text-muted">Scenario</dt>
                      <dd className="text-text-primary font-mono text-xs truncate">
                        {entry.scenario_id}
                      </dd>
                    </>
                  )}
                </dl>
              </section>

              {/* Extra meta JSON */}
              {entry.meta && Object.keys(entry.meta).length > 0 && (
                <section aria-labelledby="memory-extra-heading">
                  <h3
                    id="memory-extra-heading"
                    className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2"
                  >
                    Extra metadata
                  </h3>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    {Object.entries(entry.meta).map(([key, value]) => (
                      <div key={key} className="contents">
                        <dt className="text-text-muted">{key}</dt>
                        <dd className="text-text-primary text-xs truncate">
                          {String(value)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </section>
              )}

            </div>
          )}
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
}
