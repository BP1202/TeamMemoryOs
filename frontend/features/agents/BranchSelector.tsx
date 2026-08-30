/**
 * BranchSelector — select input for choosing a git branch.
 *
 * Fetches branch list via React Query.
 * Pure controlled component — calls onBranchChange on selection.
 */

import { useQuery } from '@tanstack/react-query';
import { listBranches } from '@services/agentsService';
import { Spinner } from '@components/ui/Spinner';

interface BranchSelectorProps {
  value: string;
  onChange: (branch: string) => void;
  id?: string;
}

export const BRANCHES_QUERY_KEY = ['agents', 'branches'] as const;

export function BranchSelector({ value, onChange, id = 'branch-selector' }: BranchSelectorProps) {
  const { data, isLoading } = useQuery({
    queryKey: BRANCHES_QUERY_KEY,
    queryFn: ({ signal }) => listBranches(signal),
    staleTime: 5 * 60 * 1000,
  });

  const branches = data?.branches ?? [];

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
          <Spinner size="sm" label="Loading branches" />
        </div>
      )}
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={isLoading}
        aria-label="Select branch"
        className="w-full px-3 py-2 text-sm rounded-md border border-border bg-surface text-text-primary
          focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
          appearance-none pr-8"
        data-testid="branch-selector"
      >
        <option value="">All branches</option>
        {branches.map((branch) => (
          <option key={branch} value={branch}>
            {branch}
          </option>
        ))}
      </select>
    </div>
  );
}
