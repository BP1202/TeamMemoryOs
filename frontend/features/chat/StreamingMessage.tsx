/**
 * StreamingMessage — animated placeholder shown while a response is being generated.
 *
 * Features:
 *   - Typing cursor animation (respects prefers-reduced-motion).
 *   - Partial Markdown rendering of streamed content (when available).
 *   - Announces completion to screen readers via aria-live.
 *
 * Architecture:
 *   - Receives partial content as prop — does not read from store.
 *   - When content is empty, shows pulsing dots.
 *   - When content is present (partial streaming), renders it with MarkdownRenderer.
 *
 * Note: Current backend returns complete responses. This component is ready for
 * future streaming without requiring backend changes.
 */

import { useEffect, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';
import { Spinner } from '@components/ui/Spinner';
import { MarkdownRenderer } from '@utils/markdownRenderer';
import { cn } from '@utils/cn';

interface StreamingMessageProps {
  /** Partial content accumulated so far. Empty while waiting for first token. */
  partialContent?: string;
  /** Label shown in the thinking indicator. */
  label?: string;
  className?: string;
}

export function StreamingMessage({
  partialContent = '',
  label = 'Thinking…',
  className,
}: StreamingMessageProps) {
  const prefersReducedMotion = useReducedMotion();
  const announcerRef = useRef<HTMLDivElement>(null);

  // Announce to screen readers when content starts arriving
  useEffect(() => {
    if (partialContent && announcerRef.current) {
      announcerRef.current.textContent = 'Response received.';
    }
  }, [partialContent]);

  return (
    <div
      className={cn('space-y-2', className)}
      aria-label="Generating response"
      aria-busy="true"
      data-testid="streaming-message"
    >
      {/* Screen reader live region */}
      <div
        ref={announcerRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />

      {/* Thinking indicator — shown while content is empty */}
      {!partialContent && (
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <Spinner size="sm" />
          <span>{label}</span>

          {/* Animated dots — suppressed under prefers-reduced-motion */}
          {!prefersReducedMotion && (
            <span className="flex items-center gap-0.5" aria-hidden="true">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1 h-1 rounded-full bg-text-muted animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </span>
          )}
        </div>
      )}

      {/* Partial content — shown as it streams in */}
      {partialContent && (
        <div className="relative text-sm text-text-primary">
          <MarkdownRenderer content={partialContent} />

          {/* Typing cursor */}
          <span
            className={cn(
              'inline-block w-0.5 h-4 bg-brand ml-0.5 align-middle',
              prefersReducedMotion ? 'opacity-100' : 'animate-pulse',
            )}
            aria-hidden="true"
          />
        </div>
      )}
    </div>
  );
}
