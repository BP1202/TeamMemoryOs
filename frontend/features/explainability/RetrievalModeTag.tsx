/**
 * RetrievalModeTag — inline tag showing the retrieval mode used.
 *
 * AI UI Contract:
 *   - Always visible inline on every Granite-powered response surface.
 *   - Never hidden or collapsed by default.
 *   - Receives data as props — no store or service reads.
 *
 * Location: features/explainability/ — not to be redefined elsewhere.
 */

import { AIIcons } from '@config/icons';
import { cn } from '@utils/cn';

interface RetrievalModeTagProps {
  /** Retrieval mode string from backend — e.g. "semantic", "hybrid", "engineering". */
  mode: string;
  className?: string;
}

function modeStyles(mode: string): string {
  switch (mode.toLowerCase()) {
    case 'hybrid':
      return 'text-brand bg-brand/10 border-brand/30';
    case 'engineering':
      return 'text-purple-600 bg-purple-50 border-purple-200 dark:text-purple-400 dark:bg-purple-900/20 dark:border-purple-800';
    default:
      // semantic
      return 'text-text-secondary bg-surface-subtle border-border';
  }
}

function modeLabel(mode: string): string {
  switch (mode.toLowerCase()) {
    case 'hybrid':      return 'Hybrid retrieval';
    case 'engineering': return 'Engineering context';
    default:            return 'Semantic search';
  }
}

export function RetrievalModeTag({ mode, className }: RetrievalModeTagProps) {
  const label  = modeLabel(mode);
  const styles = modeStyles(mode);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border',
        styles,
        className,
      )}
      aria-label={`Retrieval mode: ${label}`}
      title={`Retrieval strategy used: ${label}`}
    >
      <AIIcons.hybridRetrieval className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}
