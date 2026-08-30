/**
 * GraphLegend — entity type color legend for the graph canvas.
 * Pure display component — no store or API reads.
 */

import { EntityTypeIcons } from '@config/icons';
import { ENTITY_TYPES, ENTITY_TYPE_LABELS, ENTITY_TYPE_COLORS } from '@typedefs/graph';
import type { EntityType } from '@typedefs/graph';

export function GraphLegend() {
  return (
    <aside
      className="absolute bottom-4 left-4 z-10 bg-surface-elevated border border-border rounded-lg p-3 shadow-card"
      aria-label="Entity type legend"
    >
      <p className="text-[10px] font-semibold text-text-secondary uppercase tracking-wide mb-2">
        Legend
      </p>
      <ul className="space-y-1.5" role="list">
        {ENTITY_TYPES.map((type: EntityType) => {
          const Icon  = EntityTypeIcons[type as keyof typeof EntityTypeIcons];
          const color = ENTITY_TYPE_COLORS[type];
          const label = ENTITY_TYPE_LABELS[type];

          return (
            <li
              key={type}
              className="flex items-center gap-1.5"
              role="listitem"
            >
              {Icon && (
                <Icon
                  className="h-3.5 w-3.5 flex-shrink-0"
                  aria-hidden="true"
                  style={{ color }}
                />
              )}
              <span className="text-[11px] text-text-secondary">{label}</span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
