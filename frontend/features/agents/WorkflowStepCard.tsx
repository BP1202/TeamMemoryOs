/**
 * WorkflowStepCard — single step in the workflow execution timeline.
 *
 * Displays: agent name, status indicator, duration, memory count, citations count.
 * Pure display component — receives all data as props.
 */

import { StatusIcons } from '@config/icons';
import { cn } from '@utils/cn';
import type { WorkflowStep, WorkflowStepStatus } from '@typedefs/agents';

interface WorkflowStepCardProps {
  step: WorkflowStep;
  isLast?: boolean;
}

function statusStyles(status: WorkflowStepStatus): string {
  switch (status) {
    case 'complete': return 'text-success bg-success/10 border-success/30';
    case 'running':  return 'text-brand bg-brand/10 border-brand/30';
    case 'error':    return 'text-danger bg-danger/10 border-danger/30';
    default:         return 'text-text-muted bg-surface-subtle border-border';
  }
}

function StatusIcon({ status }: { status: WorkflowStepStatus }) {
  switch (status) {
    case 'complete': return <StatusIcons.success className="h-4 w-4 text-success" aria-hidden="true" />;
    case 'running':  return <StatusIcons.pending  className="h-4 w-4 text-brand animate-spin" aria-hidden="true" />;
    case 'error':    return <StatusIcons.error    className="h-4 w-4 text-danger" aria-hidden="true" />;
    default:         return <StatusIcons.info     className="h-4 w-4 text-text-muted" aria-hidden="true" />;
  }
}

export function WorkflowStepCard({ step, isLast = false }: WorkflowStepCardProps) {
  return (
    <li
      role="listitem"
      className="flex gap-3"
      data-testid={`workflow-step-${step.step}`}
      aria-label={`Step ${step.step}: ${step.agent.replace(/_/g, ' ')} — ${step.status}`}
    >
      {/* Left: connector + icon */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div
          className={cn(
            'w-8 h-8 rounded-full border flex items-center justify-center',
            statusStyles(step.status),
          )}
          aria-hidden="true"
        >
          <StatusIcon status={step.status} />
        </div>
        {!isLast && (
          <div
            className="w-px flex-1 mt-1 bg-border min-h-[1.5rem]"
            aria-hidden="true"
          />
        )}
      </div>

      {/* Right: content */}
      <div className="flex-1 pb-4 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-medium text-text-muted">
            Step {step.step}
          </span>
          <span className="font-semibold text-sm text-text-primary">
            {step.agent.replace(/_/g, ' ')}
          </span>

          {/* Status badge — text label ensures not color-only (WCAG 1.4.1) */}
          <span
            className={cn(
              'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border capitalize',
              statusStyles(step.status),
            )}
          >
            {step.status}
          </span>

          {step.duration_ms !== null && (
            <span className="text-[10px] text-text-muted ml-auto">
              {step.duration_ms < 1000
                ? `${step.duration_ms}ms`
                : `${(step.duration_ms / 1000).toFixed(1)}s`}
            </span>
          )}
        </div>

        <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
          {step.description}
        </p>

        {(step.memory_count > 0 || step.citations_count > 0) && (
          <div className="flex gap-3 mt-1 text-[10px] text-text-muted">
            {step.memory_count > 0 && (
              <span>{step.memory_count} memor{step.memory_count === 1 ? 'y' : 'ies'}</span>
            )}
            {step.citations_count > 0 && (
              <span>{step.citations_count} citation{step.citations_count === 1 ? '' : 's'}</span>
            )}
          </div>
        )}
      </div>
    </li>
  );
}
