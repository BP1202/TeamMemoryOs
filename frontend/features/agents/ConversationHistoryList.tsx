/**
 * ConversationHistoryList — session-persistent workflow history.
 *
 * Reads from agentStore.workflowHistory (capped at 20 turns).
 *
 * Accessibility:
 *   - role="log", aria-live="polite" for live turn updates.
 *   - Per-turn agent name visible as text.
 */

import { NavIcons, UtilityIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { EmptyState } from '@components/feedback/EmptyState';
import { useAgentStore } from '@stores/agentStore';
import { ConversationTurn } from './ConversationTurn';

export function ConversationHistoryList() {
  const history = useAgentStore((s) => s.workflowHistory);
  const clearHistory = useAgentStore((s) => s.clearWorkflowHistory);

  return (
    <div className="space-y-4" data-testid="conversation-history">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">
          Conversation History
          {history.length > 0 && (
            <span className="ml-2 text-xs font-normal text-text-muted">
              ({history.length} turn{history.length === 1 ? '' : 's'})
            </span>
          )}
        </h3>
        {history.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearHistory}
            aria-label="Clear workflow conversation history"
          >
            <UtilityIcons.Delete className="h-3.5 w-3.5" aria-hidden="true" />
            Clear
          </Button>
        )}
      </div>

      {history.length === 0 ? (
        <EmptyState
          icon={NavIcons.Agents}
          heading="No history yet"
          description="Execute a workflow to see conversation history here."
        />
      ) : (
        <div
          role="log"
          aria-live="polite"
          aria-label="Workflow conversation history"
          className="space-y-4"
        >
          {history.map((turn) => (
            <ConversationTurn key={turn.id} turn={turn} />
          ))}
        </div>
      )}
    </div>
  );
}
