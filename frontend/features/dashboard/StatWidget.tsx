/**
 * StatWidget — displays a single numeric metric.
 *
 * States: loading (skeleton), data, error.
 * Accessibility: role="status", aria-label, aria-busy.
 */

import type { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@components/ui/Card';
import { Skeleton } from '@components/ui/Skeleton';
import { cn } from '@utils/cn';

interface StatWidgetProps {
  label: string;
  value?: number;
  icon: LucideIcon;
  isLoading?: boolean;
  isError?: boolean;
  /** Optional link action text */
  href?: string;
  className?: string;
}

export function StatWidget({
  label,
  value,
  icon: Icon,
  isLoading = false,
  isError = false,
  className,
}: StatWidgetProps) {
  return (
    <Card
      variant="elevated"
      role="status"
      aria-label={`${label} count`}
      aria-busy={isLoading}
      className={cn('flex flex-col gap-3', className)}
    >
      <CardContent className="pt-0">
        <div className="flex items-start justify-between">
          <div className="space-y-1 min-w-0">
            <p className="text-xs font-medium text-text-secondary uppercase tracking-wide">
              {label}
            </p>
            {isLoading ? (
              <Skeleton className="h-8 w-16" aria-hidden="true" />
            ) : isError ? (
              <p className="text-sm text-danger">Unavailable</p>
            ) : (
              <p className="text-3xl font-bold text-text-primary" aria-live="polite">
                {value ?? '—'}
              </p>
            )}
          </div>
          <div
            className="rounded-lg p-2 bg-brand-subtle flex-shrink-0"
            aria-hidden="true"
          >
            <Icon className="h-5 w-5 text-brand" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
