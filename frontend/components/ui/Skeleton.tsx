/**
 * Skeleton — design system primitive.
 *
 * Animated placeholder for loading states.
 * Use instead of spinners when layout is known in advance.
 */

import { cn } from '@utils/cn';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'animate-pulse rounded-md bg-surface-elevated',
        className,
      )}
    />
  );
}

// ─── Preset skeletons for common patterns ─────────────────────────────────

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className={cn('h-4', i === lines - 1 ? 'w-3/4' : 'w-full')}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div
      className="rounded-lg border border-border p-6 space-y-3 bg-surface"
      aria-hidden="true"
    >
      <Skeleton className="h-5 w-2/5" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
    </div>
  );
}
