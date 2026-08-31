/**
 * HealthWidget — shows backend + database health status.
 *
 * States: loading (skeleton), data, error.
 * Accessibility: role="status", aria-label, status never by color alone.
 */

import { useQuery } from '@tanstack/react-query';
import { getHealth, getDbHealth } from '@services/healthService';
import { StatusIcons } from '@config/icons';
import { Card, CardHeader, CardTitle, CardContent } from '@components/ui/Card';
import { Skeleton } from '@components/ui/Skeleton';
import { Badge } from '@components/ui/Badge';
import type { BadgeVariant } from '@typedefs/ui';
import { cn } from '@utils/cn';

// ─── Query keys ────────────────────────────────────────────────────────────

export const HEALTH_KEY    = ['health', 'backend'] as const;
export const DB_HEALTH_KEY = ['health', 'db']      as const;

// ─── Status row ────────────────────────────────────────────────────────────

interface StatusRowProps {
  label: string;
  status: 'healthy' | 'unhealthy' | 'loading' | 'error';
  detail?: string;
}

function statusVariant(s: StatusRowProps['status']): BadgeVariant {
  if (s === 'healthy') return 'success';
  if (s === 'unhealthy' || s === 'error') return 'danger';
  return 'default';
}

function StatusRow({ label, status, detail }: StatusRowProps) {
  const Icon =
    status === 'healthy' ? StatusIcons.success :
    status === 'unhealthy' || status === 'error' ? StatusIcons.error :
    StatusIcons.pending;

  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-2">
        <Icon
          className={cn(
            'h-4 w-4',
            status === 'healthy'              ? 'text-success' :
            status === 'unhealthy' || status === 'error' ? 'text-danger' :
            'text-text-muted',
          )}
          aria-hidden="true"
        />
        <span className="text-sm text-text-primary">{label}</span>
        {detail && <span className="text-xs text-text-muted">{detail}</span>}
      </div>
      <Badge variant={statusVariant(status)}>
        {status === 'loading' ? 'Checking…' : status}
      </Badge>
    </div>
  );
}

// ─── HealthWidget ──────────────────────────────────────────────────────────

export function HealthWidget() {
  const backendQ = useQuery({
    queryKey: HEALTH_KEY,
    queryFn:  getHealth,
    staleTime: 30_000,
  });

  const dbQ = useQuery({
    queryKey: DB_HEALTH_KEY,
    queryFn:  getDbHealth,
    staleTime: 30_000,
  });

  const isLoading = backendQ.isLoading || dbQ.isLoading;

  return (
    <Card
      variant="elevated"
      role="status"
      aria-label="System health"
      aria-busy={isLoading}
    >
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3" aria-hidden="true">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : (
          <div>
            <StatusRow
              label="Backend"
              status={
                backendQ.isError ? 'error' :
                (backendQ.data?.status ?? 'unhealthy')
              }
              detail={backendQ.data?.version}
            />
            <StatusRow
              label="Database"
              status={
                dbQ.isError ? 'error' :
                (dbQ.data?.status ?? 'unhealthy')
              }
              detail={dbQ.data?.database}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
