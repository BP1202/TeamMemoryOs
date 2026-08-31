/**
 * RelationshipEdge — custom React Flow edge component.
 *
 * Renders a directed edge with:
 *   - Relationship type label in the middle
 *   - Arrow marker on the target end
 *
 * Rules:
 *   - No store reads.
 *   - Pure display component.
 */

import { memo } from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from '@xyflow/react';
import { RELATIONSHIP_TYPE_LABELS } from '@typedefs/graph';
import type { RelationshipType } from '@typedefs/graph';

// ─── Edge data shape ────────────────────────────────────────────────────────

export interface RelationshipEdgeData {
  relationship_type: RelationshipType;
}

// ─── Component ──────────────────────────────────────────────────────────────

export const RelationshipEdge = memo(function RelationshipEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: EdgeProps) {
  // data is typed as Record<string, unknown> by React Flow — cast to our shape.
  const edgeData = data as unknown as RelationshipEdgeData | undefined;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const label = edgeData?.relationship_type
    ? (RELATIONSHIP_TYPE_LABELS[edgeData.relationship_type] ?? String(edgeData.relationship_type))
    : '';

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{ stroke: 'var(--color-border-strong, #475569)', strokeWidth: 1.5 }}
      />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position:  'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'none',
            }}
            className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-surface-elevated border border-border text-text-secondary"
            aria-hidden="true"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
