/**
 * CitationPanel — displays retrieved memory citations for an AI response.
 *
 * AI UI Contract:
 *   - Always visible on every Granite-powered response surface.
 *   - Never hidden behind a toggle or collapsed by default.
 *   - Receives data as props — no store or service reads.
 *
 * Location: features/explainability/ — not to be redefined elsewhere.
 */

import { AIIcons, UtilityIcons } from '@config/icons';
import type { CitationRead } from '@typedefs/chat';
import { cn } from '@utils/cn';

interface CitationPanelProps {
  citations: CitationRead[];
  className?: string;
}

export function CitationPanel({ citations, className }: CitationPanelProps) {
  if (citations.length === 0) {
    return (
      <div
        className={cn('flex items-center gap-2 text-xs text-text-muted', className)}
        aria-label="No citations"
      >
        <AIIcons.citation className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
        <span>No citations retrieved</span>
      </div>
    );
  }

  return (
    <section
      className={cn('space-y-2', className)}
      aria-label={`${citations.length} citation${citations.length === 1 ? '' : 's'}`}
    >
      <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wide">
        <AIIcons.citation className="h-3.5 w-3.5" aria-hidden="true" />
        <span>Citations ({citations.length})</span>
      </div>

      <ol className="space-y-1.5 list-none p-0 m-0">
        {citations.map((citation) => (
          <li
            key={citation.memory_id}
            className="flex items-start gap-2 p-2 bg-surface-subtle rounded border border-border text-xs"
          >
            {/* Rank badge */}
            <span
              className="flex-shrink-0 w-5 h-5 rounded-full bg-brand/10 text-brand font-bold text-[10px] flex items-center justify-center"
              aria-hidden="true"
            >
              {citation.rank}
            </span>

            <div className="flex-1 min-w-0 space-y-0.5">
              {/* Title */}
              <p className="font-medium text-text-primary truncate">
                {citation.memory_title ?? 'Untitled memory'}
              </p>

              {/* Reason + type */}
              <p className="text-text-secondary line-clamp-1">
                {citation.retrieval_reason}
              </p>

              {/* Score + metadata */}
              <div className="flex items-center gap-3 text-text-muted flex-wrap">
                <span>Score: {(citation.final_score * 100).toFixed(0)}%</span>
                <span className="capitalize">{citation.memory_type}</span>
                {citation.matched_entities.length > 0 && (
                  <span className="flex items-center gap-1">
                    <UtilityIcons.ExternalLink className="h-3 w-3" aria-hidden="true" />
                    {citation.matched_entities.length} entit{citation.matched_entities.length === 1 ? 'y' : 'ies'}
                  </span>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
