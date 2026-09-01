/**
 * ErrorState — feedback component.
 * Shown when a query or operation fails.
 * Always includes a retry action.
 *
 * Rules:
 *   - Receives all data as props.
 *   - No store or service reads.
 */

import type { ReactNode } from 'react';
import { StatusIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { cn } from '@utils/cn';

interface ErrorStateProps {
  /** Required error heading. */
  heading?: string;
  /** Error detail message. */
  message?: string;
  /** Retry handler — required. Every error state has a retry action. */
  onRetry?: () => void;
  /** Override retry label. */
  retryLabel?: string;
  /** Additional content (e.g. a report-error link). */
  footer?: ReactNode;
  className?: string;
}

export function ErrorState({
  heading = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
  footer,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4',
        'py-16 px-6 text-center',
        className,
      )}
      role="alert"
      aria-live="assertive"
    >
      <StatusIcons.error
        className="h-12 w-12 text-danger"
        aria-hidden="true"
      />

      <div className="space-y-1">
        <h3 className="text-base font-semibold text-text-primary">{heading}</h3>
        {message && (
          <p className="text-sm text-text-secondary max-w-sm">{message}</p>
        )}
      </div>

      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          {retryLabel}
        </Button>
      )}

      {footer && <div className="mt-2">{footer}</div>}
    </div>
  );
}
