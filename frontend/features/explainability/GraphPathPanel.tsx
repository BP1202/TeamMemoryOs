/**
 * GraphPathPanel — displays the knowledge graph traversal path used in retrieval.
 *
 * AI UI Contract:
 *   - Visible when graph_path is non-empty.
 *   - Never hidden or collapsed when data is present.
 *   - Receives data as props — no store or service reads.
 *
 * Location: features/explainability/ — not to be redefined elsewhere.
 */

import { AIIcons, UtilityIcons } from '@config/icons';
import type { GraphPathStepRead } from '@typedefs/chat';
import { cn } from '@utils/cn';

interface GraphPathPanelProps {
  steps: GraphPathStepRead[];
  className?: string;
}

export function GraphPathPanel({ steps, className }: GraphPathPanelProps) {
  if (steps.length === 0) return null;

  return (
    <section
      className={cn('space-y-2', className)}
      aria-label="Knowledge graph traversal path"
    >
      <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wide">
        <AIIcons.graphPath className="h-3.5 w-3.5" aria-hidden="true" />
        <span>Graph Path ({steps.length} step{steps.length === 1 ? '' : 's'})</span>
      </div>

      <ol
        className="flex flex-wrap items-center gap-1 text-xs"
        aria-label="Graph traversal steps"
      >
        {steps.map((step, idx) => (
          <li key={`${step.source_entity_id}-${step.target_entity_id}-${idx}`} className="flex items-center gap-1">
            {/* Source entity */}
            <span
              className="px-2 py-0.5 bg-surface-subtle border border-border rounded text-text-primary font-medium"
              title={`Entity: ${step.source_entity_name}`}
            >
              {step.source_entity_name}
            </span>

            {/* Relationship arrow */}
            <span className="flex items-center gap-0.5 text-text-muted flex-shrink-0">
              <UtilityIcons.ArrowRight className="h-3 w-3" aria-hidden="true" />
              <span className="text-[10px] uppercase tracking-wide text-text-muted">
                {step.relationship_type.replace(/_/g, ' ')}
              </span>
              <UtilityIcons.ArrowRight className="h-3 w-3" aria-hidden="true" />
            </span>

            {/* Target entity — only render inline if last step */}
            {idx === steps.length - 1 && (
              <span
                className="px-2 py-0.5 bg-brand/10 border border-brand/30 rounded text-brand font-medium"
                title={`Entity: ${step.target_entity_name}`}
              >
                {step.target_entity_name}
              </span>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
