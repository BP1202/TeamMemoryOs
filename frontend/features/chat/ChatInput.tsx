/**
 * ChatInput — message composition area at the bottom of the chat.
 *
 * Features:
 *   - Textarea with auto-resize.
 *   - Submit on Enter (Shift+Enter for newline).
 *   - Disabled while a response is loading.
 *   - Hybrid retrieval toggle.
 *   - Scenario selector.
 *   - Character limit indicator.
 *
 * Rules:
 *   - Controlled by React Hook Form.
 *   - No direct state management — callbacks via props.
 *   - accessible: label, aria-describedby, role="form".
 */

import { useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@components/ui/Button';
import { UtilityIcons } from '@config/icons';
import { cn } from '@utils/cn';
import type { Scenario } from '@typedefs/memory';

const MAX_CHARS = 2000;

interface ChatInputFormValues {
  message: string;
}

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading: boolean;
  scenarios?: Scenario[];
  selectedScenarioId: string | null;
  useHybrid: boolean;
  onScenarioChange: (id: string | null) => void;
  onHybridChange: (value: boolean) => void;
}

export function ChatInput({
  onSubmit,
  isLoading,
  scenarios = [],
  selectedScenarioId,
  useHybrid,
  onScenarioChange,
  onHybridChange,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<ChatInputFormValues>({
    defaultValues: { message: '' },
  });

  const messageValue = watch('message');
  const charCount    = messageValue.length;

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [messageValue]);

  const handleFormSubmit = (data: ChatInputFormValues) => {
    const trimmed = data.message.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
    reset();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit(handleFormSubmit)();
    }
  };

  // Expose ref alongside react-hook-form registration
  const { ref: rhfRef, ...restRegister } = register('message', {
    required: 'Please enter a message',
    maxLength: {
      value: MAX_CHARS,
      message: `Message must be ${MAX_CHARS} characters or fewer`,
    },
  });

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      aria-label="Chat message input"
      className="border-t border-border bg-surface p-4 space-y-3"
    >
      {/* Options row */}
      <div className="flex items-center gap-4 flex-wrap text-xs text-text-secondary">
        {/* Scenario selector */}
        {scenarios.length > 0 && (
          <label className="flex items-center gap-2">
            <span className="font-medium">Scenario:</span>
            <select
              value={selectedScenarioId ?? ''}
              onChange={(e) => onScenarioChange(e.target.value || null)}
              disabled={isLoading}
              className={cn(
                'text-xs bg-surface-subtle border border-border rounded px-2 py-1',
                'focus:outline-none focus:ring-2 focus:ring-brand',
                'disabled:opacity-50',
              )}
              aria-label="Filter by scenario"
            >
              <option value="">All scenarios</option>
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
        )}

        {/* Hybrid retrieval toggle */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={useHybrid}
            onChange={(e) => onHybridChange(e.target.checked)}
            disabled={isLoading}
            className="rounded border-border focus:ring-brand disabled:opacity-50"
            aria-label="Use hybrid retrieval (semantic + knowledge graph)"
            id="hybrid-toggle"
          />
          <span className="font-medium" aria-hidden="true">
            Hybrid retrieval
          </span>
        </label>
      </div>

      {/* Textarea + send button */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative" role="search">
          <label htmlFor="chat-message-input" className="sr-only">
            Type your question
          </label>
          <textarea
            id="chat-message-input"
            {...restRegister}
            ref={(el) => {
              rhfRef(el);
              (textareaRef as React.MutableRefObject<HTMLTextAreaElement | null>).current = el;
            }}
            placeholder="Ask about your team's knowledge… (Enter to send, Shift+Enter for newline)"
            disabled={isLoading}
            onKeyDown={handleKeyDown}
            rows={1}
            className={cn(
              'w-full resize-none rounded-lg border bg-surface px-3 py-2.5 text-sm',
              'placeholder:text-text-muted text-text-primary leading-relaxed',
              'focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent',
              'disabled:opacity-60 disabled:cursor-not-allowed',
              errors.message ? 'border-danger' : 'border-border',
            )}
            aria-describedby={errors.message ? 'chat-message-error' : 'chat-char-count'}
            aria-invalid={Boolean(errors.message)}
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading || !messageValue.trim()}
          aria-label="Send message"
          className="flex-shrink-0 mb-0.5"
          size="md"
        >
          {isLoading ? (
            <UtilityIcons.Loading className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <UtilityIcons.ArrowRight className="h-4 w-4" aria-hidden="true" />
          )}
          <span className="sr-only">Send</span>
        </Button>
      </div>

      {/* Character count + validation */}
      <div className="flex items-center justify-between text-xs">
        {errors.message ? (
          <p
            id="chat-message-error"
            className="text-danger"
            role="alert"
            aria-live="polite"
          >
            {errors.message.message}
          </p>
        ) : (
          <span id="chat-char-count" className="text-text-muted" aria-live="polite">
            {charCount > 0 ? `${charCount} / ${MAX_CHARS}` : ''}
          </span>
        )}
      </div>
    </form>
  );
}
