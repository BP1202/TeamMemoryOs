/**
 * ConfidenceBadge — inline badge showing the Granite confidence score.
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

interface ConfidenceBadgeProps {
  /** Confidence score from 0.0 to 1.0. */
  score: number;
  className?: string;
}

/** Returns Tailwind color classes based on confidence threshold. */
function confidenceColor(score: number): string {
  if (score >= 0.75) return 'text-success bg-success/10 border-success/30';
  if (score >= 0.50) return 'text-warning bg-warning/10 border-warning/30';
  return 'text-danger bg-danger/10 border-danger/30';
}

/** Human-readable label for confidence tiers. */
function confidenceLabel(score: number): string {
  if (score >= 0.75) return 'High';
  if (score >= 0.50) return 'Medium';
  return 'Low';
}

export function ConfidenceBadge({ score, className }: ConfidenceBadgeProps) {
  const pct   = Math.round(score * 100);
  const color = confidenceColor(score);
  const label = confidenceLabel(score);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border',
        color,
        className,
      )}
      aria-label={`Confidence: ${label} (${pct}%)`}
      title={`AI confidence score: ${pct}% — ${label}`}
    >
      <AIIcons.confidence className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
      <span>{pct}%</span>
      {/* Text label ensures status is not communicated by color alone (WCAG 1.4.1) */}
      <span className="sr-only">{label} confidence</span>
    </span>
  );
}
