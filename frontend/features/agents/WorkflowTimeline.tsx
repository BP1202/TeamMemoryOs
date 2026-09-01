/**
 * WorkflowTimeline — ordered vertical timeline of workflow execution steps.
 *
 * Displays 6 steps: Planner → Repository Agent → Debug Agent →
 *   Retriever → Granite → Explanation Builder
 *
 * Accessibility:
 *   - role="list" on the container
 *   - Each step has role="listitem" (in WorkflowStepCard)
 *
 * Pure display component — receives all data as props.
 */

import { WorkflowStepCard } from './WorkflowStepCard';
import type { WorkflowStep } from '@typedefs/agents';
import { cn } from '@utils/cn';

interface WorkflowTimelineProps {
  steps: WorkflowStep[];
  className?: string;
}

export function WorkflowTimeline({ steps, className }: WorkflowTimelineProps) {
  if (steps.length === 0) return null;

  return (
    <section
      className={cn('space-y-0', className)}
      aria-label={`Workflow timeline — ${steps.length} steps`}
    >
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
        Execution Timeline
      </h3>

      <ol
        role="list"
        className="space-y-0"
        aria-label="Workflow execution steps"
        data-testid="workflow-timeline"
      >
        {steps.map((step, idx) => (
          <WorkflowStepCard
            key={step.step}
            step={step}
            isLast={idx === steps.length - 1}
          />
        ))}
      </ol>
    </section>
  );
}
