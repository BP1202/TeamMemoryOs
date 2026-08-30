/**
 * MessageBubble — renders a single chat message (user or assistant).
 *
 * Architecture (post-refactor):
 *   - UserBubble: plain text in a brand-colored pill.
 *   - AssistantBubble: delegates ALL assistant rendering to AIResponseCard.
 *     This component is now a lightweight role-switcher only.
 *   - Loading/error states remain here (they precede AIResponseCard content).
 *
 * Rules:
 *   - Pure display component — receives all data as props.
 *   - No store or service reads.
 *   - No dangerouslySetInnerHTML.
 */

import { AIIcons, NavIcons } from '@config/icons';
import { AIResponseCard } from './AIResponseCard';
import { StreamingMessage } from './StreamingMessage';
import type { ChatMessage } from '@typedefs/chat';
import { cn } from '@utils/cn';

interface MessageBubbleProps {
  message: ChatMessage;
  onSuggestedAction?: (action: string) => void;
}

// ─── User bubble ─────────────────────────────────────────────────────────────

function UserBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="flex justify-end" data-testid="message-user">
      <div
        className={cn(
          'max-w-[80%] px-4 py-3 rounded-2xl rounded-tr-sm',
          'bg-brand text-white text-sm leading-relaxed',
        )}
      >
        {/* Plain text — user messages are never rendered as Markdown */}
        <p>{message.content}</p>
      </div>
    </div>
  );
}

// ─── Assistant bubble ─────────────────────────────────────────────────────────

function AssistantBubble({
  message,
  onSuggestedAction,
}: {
  message: ChatMessage;
  onSuggestedAction?: (action: string) => void;
}) {
  return (
    <div className="flex gap-3 items-start" data-testid="message-assistant">
      {/* Granite avatar */}
      <div
        className="flex-shrink-0 w-8 h-8 rounded-full bg-brand/10 flex items-center justify-center mt-0.5"
        aria-hidden="true"
      >
        <AIIcons.granite className="h-4 w-4 text-brand" aria-hidden="true" />
      </div>

      <div className="flex-1 min-w-0">
        {/* Loading / streaming state */}
        {message.isLoading && !message.content && (
          <StreamingMessage label="Thinking…" />
        )}

        {/* Streaming in progress with partial content */}
        {message.isLoading && message.content && (
          <StreamingMessage partialContent={message.content} />
        )}

        {/* Error state */}
        {message.error && !message.isLoading && (
          <div
            className="flex items-center gap-2 text-sm text-danger"
            role="alert"
            aria-live="assertive"
          >
            <NavIcons.Chat className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <span>{message.error}</span>
          </div>
        )}

        {/* Completed response — delegated entirely to AIResponseCard */}
        {!message.isLoading && !message.error && message.content && (
          <AIResponseCard
            content={message.content}
            explanation={message.explanation}
            created_at={message.created_at}
            suggested_actions={message.suggested_actions}
            onSuggestedAction={onSuggestedAction}
            data-testid="explainability-panel"
          />
        )}
      </div>
    </div>
  );
}

// ─── Exported component ───────────────────────────────────────────────────────

export function MessageBubble({ message, onSuggestedAction }: MessageBubbleProps) {
  if (message.role === 'user') {
    return <UserBubble message={message} />;
  }
  return (
    <AssistantBubble message={message} onSuggestedAction={onSuggestedAction} />
  );
}
