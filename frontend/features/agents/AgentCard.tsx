/**
 * AgentCard — displays a single agent from the registry.
 *
 * Pure display component — receives all data as props.
 * No store or service reads.
 */

import { NavIcons } from '@config/icons';
import { Badge } from '@components/ui/Badge';
import { Card, CardContent } from '@components/ui/Card';
import { cn } from '@utils/cn';
import type { AgentRead } from '@typedefs/agents';

interface AgentCardProps {
  agent: AgentRead;
  isSelected?: boolean;
  onSelect?: (name: string) => void;
}

export function AgentCard({ agent, isSelected = false, onSelect }: AgentCardProps) {
  return (
    <Card
      className={cn(
        'cursor-pointer transition-all duration-fast hover:shadow-md',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
        isSelected && 'ring-2 ring-brand border-brand',
      )}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      aria-label={`Agent: ${agent.name.replace(/_/g, ' ')}`}
      onClick={() => onSelect?.(agent.name)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect?.(agent.name);
        }
      }}
      data-testid={`agent-card-${agent.name}`}
    >
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div
              className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center flex-shrink-0 dark:bg-purple-900/20"
              aria-hidden="true"
            >
              <NavIcons.Agents className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="font-semibold text-sm text-text-primary truncate">
              {agent.name.replace(/_/g, ' ')}
            </h3>
          </div>

          <Badge
            variant={agent.is_active ? 'success' : 'default'}
            aria-label={agent.is_active ? 'Active' : 'Inactive'}
          >
            {agent.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Description */}
        <p className="text-xs text-text-secondary line-clamp-2">
          {agent.description}
        </p>

        {/* Capabilities */}
        {agent.capabilities.length > 0 && (
          <ul
            className="flex flex-wrap gap-1"
            aria-label="Agent capabilities"
          >
            {agent.capabilities.map((cap) => (
              <li key={cap.name}>
                <span
                  className="inline-flex px-1.5 py-0.5 text-[10px] font-medium bg-surface-subtle border border-border rounded text-text-muted"
                  title={cap.description}
                >
                  {cap.name.replace(/_/g, ' ')}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
