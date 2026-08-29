/**
 * LoadingState — feedback component.
 * Full-container loading placeholder.
 * Use when the entire content area is loading (initial load).
 *
 * For known layouts, prefer SkeletonCard / SkeletonText from components/ui/Skeleton.
 */

import { Spinner } from '@components/ui/Spinner';
import { cn } from '@utils/cn';

interface LoadingStateProps {
  label?: string;
  className?: string;
}

export function LoadingState({
  label = 'Loading…',
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3',
        'py-16 px-6',
        className,
      )}
      aria-busy="true"
      aria-label={label}
    >
      <Spinner size="lg" label={label} />
      <p className="text-sm text-text-muted">{label}</p>
    </div>
  );
}
