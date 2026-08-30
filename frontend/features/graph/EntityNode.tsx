/**
 * EntityNode — custom React Flow node component.
 *
 * Renders an entity with:
 *   - Icon from EntityTypeIcons registry
 *   - Entity name (truncated)
 *   - Type label with color
 *   - Color border from ENTITY_TYPE_COLORS
 *
 * Rules:
 *   - No store reads (React Flow injects data via `data` prop).
 *   - No API calls.
 *   - Pure display component.
 */

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { EntityTypeIcons } from '@config/icons';
import { ENTITY_TYPE_COLORS, ENTITY_TYPE_LABELS } from '@typedefs/graph';
import { cn } from '@utils/cn';
import type { Entity } from '@typedefs/graph';

// ─── Node data shape ───────────────────────────────────────────────────────

export interface EntityNodeData {
  entity: Entity;
  isSelected: boolean;
  isExpanded: boolean;
  isHighlighted: boolean;
}

// ─── Component ─────────────────────────────────────────────────────────────

export const EntityNode = memo(function EntityNode({ data }: NodeProps) {
  // data is typed as Record<string, unknown> by React Flow — cast to our shape.
  const nodeData = data as unknown as EntityNodeData;
  const { entity, isSelected, isHighlighted } = nodeData;

  if (!entity) return null;

  const Icon  = EntityTypeIcons[entity.entity_type as keyof typeof EntityTypeIcons];
  const color = ENTITY_TYPE_COLORS[entity.entity_type] ?? '#64748b';
  const label = ENTITY_TYPE_LABELS[entity.entity_type] ?? entity.entity_type;

  return (
    <div
      role="button"
      aria-label={`Entity: ${entity.name}, type: ${label}`}
      aria-pressed={isSelected}
      className={cn(
        'relative flex flex-col items-center gap-1.5',
        'px-3 py-2.5 rounded-lg min-w-[100px] max-w-[140px]',
        'bg-surface-elevated border-2 shadow-card',
        'cursor-pointer select-none',
        'transition-all duration-fast',
        isSelected
          ? 'border-brand shadow-glow ring-2 ring-brand/30'
          : 'border-border hover:border-brand/50',
        isHighlighted && !isSelected && 'ring-2 ring-amber-400/60',
      )}
      style={{ borderColor: isSelected ? undefined : `${color}66` }}
    >
      <Handle
        type="source"
        position={Position.Top}
        className="!w-2 !h-2 !bg-border !border-border"
      />

      {Icon && (
        <Icon
          className="h-5 w-5 flex-shrink-0"
          aria-hidden="true"
          style={{ color }}
        />
      )}

      <span
        className="text-xs font-medium text-text-primary text-center leading-tight line-clamp-2"
        title={entity.name}
      >
        {entity.name}
      </span>

      <span
        className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
        style={{ background: `${color}22`, color }}
        aria-label={`Type: ${label}`}
      >
        {label}
      </span>

      <Handle
        type="target"
        position={Position.Bottom}
        className="!w-2 !h-2 !bg-border !border-border"
      />
    </div>
  );
});
