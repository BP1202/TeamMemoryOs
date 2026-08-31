/**
 * EmptyState — feedback component.
 * Shown when a query returns zero items.
 *
 * Rules:
 *   - Receives all data as props.
 *   - No store or service reads.
 */

import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@utils/cn';

interface EmptyStateProps {
  /** Icon displayed above the heading. */
  icon?: LucideIcon;
  /** Required heading text. */
  heading: string;
  /** Optional explanatory body text. */
  description?: string;
  /** Optional CTA content (Button, link, etc.). */
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  heading,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4',
        'py-16 px-6 text-center',
        className,
      )}
      role="status"
      aria-label={heading}
    >
      {Icon && (
        <Icon
          className="h-12 w-12 text-text-muted"
          aria-hidden="true"
        />
      )}

      <div className="space-y-1">
        <h3 className="text-base font-semibold text-text-primary">{heading}</h3>
        {description && (
          <p className="text-sm text-text-secondary max-w-sm">{description}</p>
        )}
      </div>

      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
