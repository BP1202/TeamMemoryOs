/**
 * CommitSummaryList — displays a list of commit summaries.
 *
 * Pure display component — receives all data as props.
 */

import { UtilityIcons } from '@config/icons';
import { cn } from '@utils/cn';
import type { CommitSummary } from '@typedefs/agents';

interface CommitSummaryListProps {
  commits: CommitSummary[];
  className?: string;
}

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(iso));
}

export function CommitSummaryList({ commits, className }: CommitSummaryListProps) {
  if (commits.length === 0) {
    return (
      <p className={cn('text-xs text-text-muted', className)}>
        No commits found.
      </p>
    );
  }

  return (
    <ol
      className={cn('space-y-2', className)}
      aria-label={`${commits.length} commits`}
      data-testid="commit-summary-list"
    >
      {commits.map((commit) => (
        <li
          key={commit.sha}
          className="flex items-start gap-2 p-2.5 bg-surface-subtle rounded border border-border"
        >
          {/* SHA badge */}
          <code
            className="flex-shrink-0 text-[10px] font-mono px-1.5 py-0.5 bg-surface-elevated rounded border border-border text-text-muted"
            title={`Commit ${commit.sha}`}
          >
            {commit.sha.slice(0, 7)}
          </code>

          <div className="flex-1 min-w-0 space-y-0.5">
            {/* Message */}
            <p className="text-xs font-medium text-text-primary line-clamp-2">
              {commit.message}
            </p>

            {/* Meta */}
            <div className="flex items-center gap-3 text-[10px] text-text-muted flex-wrap">
              <span>{commit.author}</span>
              <span>{formatDate(commit.date)}</span>
              {commit.files_changed > 0 && (
                <span className="flex items-center gap-0.5">
                  <UtilityIcons.Edit className="h-3 w-3" aria-hidden="true" />
                  {commit.files_changed} file{commit.files_changed === 1 ? '' : 's'}
                </span>
              )}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
