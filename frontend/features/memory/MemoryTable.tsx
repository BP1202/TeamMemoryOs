/**
 * MemoryTable — sortable, keyboard-navigable list of memory entries.
 *
 * Columns: Title/Content, Type, Scenario, Created At
 * Clicking a row opens MemoryDetailDrawer via memoryStore.
 *
 * Rules:
 *   - Receives data as props.
 *   - Calls openDetailDrawer from memoryStore on row click.
 *   - No direct API calls.
 */

import { useCallback } from 'react';
import { MemoryTypeBadge } from './MemoryTypeBadge';
import { useMemoryStore } from '@stores/memoryStore';
import { cn } from '@utils/cn';
import type { MemoryEntry, Scenario } from '@typedefs/memory';

// ─── Props ─────────────────────────────────────────────────────────────────

interface MemoryTableProps {
  entries: MemoryEntry[];
  scenarios: Scenario[];
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year:  'numeric',
    month: 'short',
    day:   'numeric',
  });
}

function scenarioName(
  scenarioId: string | null,
  scenarios: Scenario[],
): string {
  if (!scenarioId) return '—';
  return scenarios.find((s) => s.id === scenarioId)?.name ?? '—';
}

// ─── Component ─────────────────────────────────────────────────────────────

export function MemoryTable({ entries, scenarios }: MemoryTableProps) {
  const openDetailDrawer = useMemoryStore((s) => s.openDetailDrawer);

  const handleRowClick = useCallback(
    (id: string) => openDetailDrawer(id),
    [openDetailDrawer],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTableRowElement>, id: string) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openDetailDrawer(id);
      }
    },
    [openDetailDrawer],
  );

  return (
    <div className="overflow-x-auto" role="region" aria-label="Memory entries table">
      <table
        className="w-full text-sm"
        role="table"
        aria-label="Memory entries"
      >
        <thead>
          <tr className="border-b border-border bg-surface-elevated">
            <th
              scope="col"
              className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide w-[40%]"
            >
              Title / Content
            </th>
            <th
              scope="col"
              className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide"
            >
              Type
            </th>
            <th
              scope="col"
              className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide"
            >
              Scenario
            </th>
            <th
              scope="col"
              className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide"
            >
              Created
            </th>
          </tr>
        </thead>

        <tbody>
          {entries.map((entry) => (
            <tr
              key={entry.id}
              tabIndex={0}
              role="row"
              aria-label={`Open memory: ${entry.title ?? entry.content.slice(0, 60)}`}
              className={cn(
                'border-b border-border',
                'hover:bg-surface-subtle cursor-pointer',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand',
                'transition-colors duration-fast',
              )}
              onClick={() => handleRowClick(entry.id)}
              onKeyDown={(e) => handleKeyDown(e, entry.id)}
            >
              {/* Title / Content */}
              <td className="px-4 py-3 max-w-0">
                <p className="font-medium text-text-primary truncate">
                  {entry.title ?? '(untitled)'}
                </p>
                <p className="text-xs text-text-muted truncate mt-0.5">
                  {entry.content.slice(0, 100)}
                </p>
              </td>

              {/* Type badge */}
              <td className="px-4 py-3 whitespace-nowrap">
                <MemoryTypeBadge type={entry.memory_type} />
              </td>

              {/* Scenario */}
              <td className="px-4 py-3 text-text-secondary whitespace-nowrap">
                {scenarioName(entry.scenario_id, scenarios)}
              </td>

              {/* Created At */}
              <td className="px-4 py-3 text-text-muted whitespace-nowrap">
                {formatDate(entry.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
