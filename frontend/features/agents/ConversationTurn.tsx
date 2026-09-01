/**
 * ConversationTurn — single turn in workflow conversation history.
 *
 * Displays: question, answer, agent attribution, metrics.
 * Pure display component — receives all data as props.
 *
 * Accessibility:
 *   - Role and aria-label from parent ConversationHistoryList (role="log").
 *   - Agent names visible as text (not color-only).
 */

import { AIResponseCard } from '@features/chat/AIResponseCard';
import { ParticipatingAgentsList } from '@features/explainability/ParticipatingAgentsList';
import { ExecutionMetricsBadge } from './ExecutionMetricsBadge';
import type { WorkflowHistoryTurn } from '@typedefs/agents';
import { cn } from '@utils/cn';

interface ConversationTurnProps {
  turn: WorkflowHistoryTurn;
  className?: string;
}

function formatTimestamp(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

export function ConversationTurn({ turn, className }: ConversationTurnProps) {
  return (
    <article
      className={cn('space-y-3 p-4 rounded-lg border border-border bg-surface', className)}
      aria-label={`Workflow turn: ${turn.question}`}
      data-testid="conversation-turn"
    >
      {/* Question row */}
      <header className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-text-primary flex-1 min-w-0">
          {turn.question}
        </p>
        <div className="flex items-center gap-2 flex-shrink-0">
          <ExecutionMetricsBadge durationMs={turn.response.total_duration_ms} />
          <time
            dateTime={turn.created_at}
            className="text-[10px] text-text-muted"
          >
            {formatTimestamp(turn.created_at)}
          </time>
        </div>
      </header>

      {/* Agent attribution */}
      {turn.response.participating_agents.length > 0 && (
        <ParticipatingAgentsList agents={turn.response.participating_agents} />
      )}

      {/* AI response with explainability */}
      <AIResponseCard
        content={turn.response.answer}
        explanation={turn.response.explanation}
        provider_used={turn.response.provider_used}
        created_at={turn.created_at}
        suggested_actions={turn.response.suggested_actions}
        participating_agents={turn.response.participating_agents}
      />
    </article>
  );
}
