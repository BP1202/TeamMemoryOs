/**
 * ParsedTraceView — renders a stack trace as plain text.
 *
 * Stack trace content is plain text — never rendered as HTML.
 * For large traces, shows the first VISIBLE_LINES lines with a "Show more" toggle.
 */

import { useState } from 'react';
import { Button } from '@components/ui/Button';
import { cn } from '@utils/cn';

const VISIBLE_LINES = 20;

interface ParsedTraceViewProps {
  trace: string;
  className?: string;
}

export function ParsedTraceView({ trace, className }: ParsedTraceViewProps) {
  const lines = trace.split('\n');
  const isTruncatable = lines.length > VISIBLE_LINES;
  const [expanded, setExpanded] = useState(false);

  const visibleLines = isTruncatable && !expanded
    ? lines.slice(0, VISIBLE_LINES)
    : lines;

  return (
    <div className={cn('space-y-2', className)}>
      <pre
        className={cn(
          'text-xs font-mono bg-surface-subtle rounded border border-border',
          'p-3 overflow-x-auto whitespace-pre-wrap break-all',
          'text-text-primary leading-relaxed',
        )}
        aria-label="Stack trace output"
        data-testid="parsed-trace-view"
      >
        {visibleLines.join('\n')}
        {isTruncatable && !expanded && (
          <span className="text-text-muted" aria-hidden="true">
            {'\n'}… {lines.length - VISIBLE_LINES} more lines
          </span>
        )}
      </pre>

      {isTruncatable && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Collapse stack trace' : 'Expand full stack trace'}
        >
          {expanded ? 'Show less' : `Show all ${lines.length} lines`}
        </Button>
      )}
    </div>
  );
}
