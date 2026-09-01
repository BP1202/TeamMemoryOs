/**
 * GraphFallbackTable — accessible list fallback below the graph canvas.
 *
 * Renders all entities and their outgoing relationships as a searchable table.
 * Required for screen reader and keyboard-only accessibility.
 *
 * Rules:
 *   - Receives data as props.
 *   - No store or API reads.
 */

import { EntityTypeIcons } from '@config/icons';
import { ENTITY_TYPE_LABELS, ENTITY_TYPE_COLORS } from '@typedefs/graph';
import type { Entity, Relationship } from '@typedefs/graph';
import { cn } from '@utils/cn';

// ─── Props ─────────────────────────────────────────────────────────────────

interface GraphFallbackTableProps {
  entities:      Entity[];
  relationships: Relationship[];
  onSelectEntity: (id: string) => void;
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

// ─── Component ─────────────────────────────────────────────────────────────

export function GraphFallbackTable({
  entities,
  relationships,
  onSelectEntity,
}: GraphFallbackTableProps) {
  return (
    <section aria-labelledby="graph-fallback-heading" className="mt-6">
      <h2
        id="graph-fallback-heading"
        className="text-sm font-semibold text-text-secondary mb-3"
      >
        Accessible entity list
        <span className="ml-2 text-xs text-text-muted font-normal">
          ({entities.length} entities, {relationships.length} relationships)
        </span>
      </h2>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm" role="table" aria-label="Entities">
          <thead>
            <tr className="border-b border-border bg-surface-elevated">
              <th scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide">
                Name
              </th>
              <th scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide">
                Type
              </th>
              <th scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide">
                Description
              </th>
              <th scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wide">
                Added
              </th>
            </tr>
          </thead>
          <tbody>
            {entities.map((entity) => {
              const Icon  = EntityTypeIcons[entity.entity_type as keyof typeof EntityTypeIcons];
              const color = ENTITY_TYPE_COLORS[entity.entity_type] ?? '#64748b';
              const label = ENTITY_TYPE_LABELS[entity.entity_type] ?? entity.entity_type;

              return (
                <tr
                  key={entity.id}
                  tabIndex={0}
                  role="row"
                  aria-label={`${entity.name} — ${label}`}
                  className={cn(
                    'border-b border-border hover:bg-surface-subtle cursor-pointer',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand',
                    'transition-colors duration-fast',
                  )}
                  onClick={() => onSelectEntity(entity.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectEntity(entity.id);
                    }
                  }}
                >
                  <td className="px-4 py-3 font-medium text-text-primary flex items-center gap-2">
                    {Icon && (
                      <Icon className="h-4 w-4 flex-shrink-0" aria-hidden="true" style={{ color }} />
                    )}
                    {entity.name}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="px-1.5 py-0.5 rounded text-xs font-medium"
                      style={{ background: `${color}22`, color }}
                    >
                      {label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-text-secondary max-w-xs truncate">
                    {entity.description ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-text-muted whitespace-nowrap">
                    {formatDate(entity.created_at)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
