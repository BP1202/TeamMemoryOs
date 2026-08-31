/**
 * ExecutionMetricsBadge — shows response time for a workflow run.
 *
 * Pure display component — receives all data as props.
 */

import { StatusIcons } from '@config/icons';
import { cn } from '@utils/cn';

interface ExecutionMetricsBadgeProps {
  durationMs: number | null;
  className?: string;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function ExecutionMetricsBadge({ durationMs, className }: ExecutionMetricsBadgeProps) {
  if (durationMs === null) return null;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
        'bg-surface-subtle border border-border text-text-secondary',
        className,
      )}
      aria-label={`Execution time: ${formatDuration(durationMs)}`}
      data-testid="execution-metrics-badge"
    >
      <StatusIcons.pending className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
      <span>{formatDuration(durationMs)}</span>
    </span>
  );
}
