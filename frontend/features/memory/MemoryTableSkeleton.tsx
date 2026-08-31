/**
 * MemoryTableSkeleton — loading placeholder for the memory table.
 * Renders N skeleton rows to match expected layout.
 */

import { Skeleton } from '@components/ui/Skeleton';

interface MemoryTableSkeletonProps {
  rows?: number;
}

export function MemoryTableSkeleton({ rows = 8 }: MemoryTableSkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Loading memories…"
      aria-busy="true"
      className="space-y-0"
    >
      {/* Header */}
      <div className="grid grid-cols-[2fr_1fr_1fr_120px] gap-4 px-4 py-2.5 border-b border-border">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-24" />
      </div>

      {/* Rows */}
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          className="grid grid-cols-[2fr_1fr_1fr_120px] gap-4 px-4 py-3 border-b border-border"
          aria-hidden="true"
        >
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  );
}
