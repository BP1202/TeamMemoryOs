/**
 * WorkflowPlanPreview — dry-run plan preview before workflow execution.
 *
 * Accessibility: Labelled "Preview — not executed" in visible text + aria-label.
 * Pure display component — receives all data as props.
 */

import { StatusIcons } from '@config/icons';
import { cn } from '@utils/cn';
import type { WorkflowPlanPreviewResponse } from '@typedefs/agents';

interface WorkflowPlanPreviewProps {
  plan: WorkflowPlanPreviewResponse;
  className?: string;
}

export function WorkflowPlanPreview({ plan, className }: WorkflowPlanPreviewProps) {
  return (
    <section
      className={cn(
        'p-4 rounded-lg border border-amber-200 bg-amber-50 space-y-3',
        'dark:bg-amber-900/10 dark:border-amber-800',
        className,
      )}
      aria-label="Preview only — not yet executed"
      data-testid="workflow-plan-preview"
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <StatusIcons.info className="h-4 w-4 text-amber-600 flex-shrink-0" aria-hidden="true" />
        <span className="text-xs font-semibold text-amber-700 dark:text-amber-300 uppercase tracking-wide">
          Preview — not yet executed
        </span>
        {plan.estimated_total_ms !== null && (
          <span className="ml-auto text-xs text-amber-600 dark:text-amber-400">
            ~{(plan.estimated_total_ms / 1000).toFixed(1)}s estimated
          </span>
        )}
      </div>

      {/* Question */}
      <p className="text-sm text-text-primary font-medium line-clamp-2">
        "{plan.question}"
      </p>

      {/* Selected agents */}
      {plan.selected_agents.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {plan.selected_agents.map((agent) => (
            <span
              key={agent}
              className="inline-flex px-2 py-0.5 text-xs font-medium bg-purple-50 border border-purple-200 rounded text-purple-700 dark:bg-purple-900/20 dark:border-purple-800 dark:text-purple-300"
            >
              {agent.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Plan steps */}
      <ol
        className="space-y-2"
        aria-label="Planned workflow steps"
      >
        {plan.steps.map((step) => (
          <li
            key={step.step}
            className="flex items-start gap-2 text-xs"
          >
            <span
              className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 font-bold text-[10px] flex items-center justify-center mt-0.5"
              aria-hidden="true"
            >
              {step.step}
            </span>
            <div className="flex-1 min-w-0">
              <span className="font-medium text-text-primary">
                {step.agent.replace(/_/g, ' ')}
              </span>
              <span className="text-text-secondary ml-1">— {step.description}</span>
              {step.estimated_duration_ms !== null && (
                <span className="ml-2 text-text-muted">
                  (~{step.estimated_duration_ms < 1000
                    ? `${step.estimated_duration_ms}ms`
                    : `${(step.estimated_duration_ms / 1000).toFixed(1)}s`})
                </span>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
