/**
 * ParticipatingAgentsList — shows which agents contributed to the response.
 *
 * AI UI Contract:
 *   - Visible when the list is non-empty.
 *   - Never hidden when data is present.
 *   - Receives data as props — no store or service reads.
 *
 * Location: features/explainability/ — not to be redefined elsewhere.
 */

import { AIIcons } from '@config/icons';
import { cn } from '@utils/cn';

interface ParticipatingAgentsListProps {
  agents: string[];
  className?: string;
}

export function ParticipatingAgentsList({ agents, className }: ParticipatingAgentsListProps) {
  if (agents.length === 0) return null;

  return (
    <section
      className={cn('space-y-1.5', className)}
      aria-label="Participating agents"
    >
      <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wide">
        <AIIcons.granite className="h-3.5 w-3.5" aria-hidden="true" />
        <span>Agents ({agents.length})</span>
      </div>

      <ul className="flex flex-wrap gap-1.5" aria-label="List of participating agents">
        {agents.map((agent) => (
          <li key={agent}>
            <span
              className="inline-flex items-center px-2 py-0.5 bg-purple-50 border border-purple-200 rounded text-xs text-purple-700 font-medium dark:bg-purple-900/20 dark:border-purple-800 dark:text-purple-300"
              title={`Agent: ${agent}`}
            >
              {agent.replace(/_/g, ' ')}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
