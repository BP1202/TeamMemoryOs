/**
 * AIWorkspaceHeader — reusable workspace header for AI-powered surfaces.
 *
 * Used by:
 *   - AI Chat Workspace (ChatPage)
 *   - Engineering Copilot (Sprint 8.5)
 *   - Multi-Agent Workspace (Sprint 8.5)
 *
 * Contains:
 *   - Workspace title + icon.
 *   - Retrieval mode selector (semantic / hybrid).
 *   - Organization badge.
 *   - Granite provider badge.
 *   - Optional clear conversation action.
 *
 * Rules:
 *   - Pure display component — all state is passed as props.
 *   - No store or service reads.
 *   - Accessible: all controls have labels.
 */

import type { LucideIcon } from 'lucide-react';
import { AIIcons, UtilityIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { cn } from '@utils/cn';

export type RetrievalModeOption = 'semantic' | 'hybrid';

interface AIWorkspaceHeaderProps {
  /** Page title shown in the header. */
  title: string;
  /** Optional subtitle / description. */
  description?: string;
  /** Icon for the workspace — from NavIcons. */
  icon?: LucideIcon;
  /** Name of the authenticated organization. */
  organizationName?: string;
  /** Current retrieval mode. */
  retrievalMode: RetrievalModeOption;
  /** Callback when the user toggles retrieval mode. */
  onRetrievalModeChange: (mode: RetrievalModeOption) => void;
  /** Whether a conversation is in progress (shows the clear button). */
  hasConversation?: boolean;
  /** Callback for clear conversation. */
  onClear?: () => void;
  /** Whether a request is in-flight (disables mode selector). */
  isLoading?: boolean;
  className?: string;
}

export function AIWorkspaceHeader({
  title,
  description,
  icon: Icon,
  organizationName,
  retrievalMode,
  onRetrievalModeChange,
  hasConversation = false,
  onClear,
  isLoading = false,
  className,
}: AIWorkspaceHeaderProps) {
  return (
    <header
      className={cn(
        'flex items-center gap-4 px-6 py-4 border-b border-border flex-shrink-0 flex-wrap',
        className,
      )}
      aria-label={`${title} workspace header`}
    >
      {/* Title + description */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        {Icon && (
          <Icon className="h-5 w-5 text-brand flex-shrink-0" aria-hidden="true" />
        )}
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-text-primary leading-tight">
            {title}
          </h1>
          {description && (
            <p className="text-xs text-text-secondary mt-0.5 truncate">
              {description}
            </p>
          )}
        </div>
      </div>

      {/* Right-side controls */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Granite provider badge */}
        <span
          className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-brand/10 text-brand border border-brand/20"
          aria-label="Powered by IBM Granite"
          title="IBM Granite — enterprise AI model"
        >
          <AIIcons.granite className="h-3 w-3" aria-hidden="true" />
          IBM Granite
        </span>

        {/* Organization badge */}
        {organizationName && (
          <span
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-surface-subtle border border-border text-text-secondary"
            aria-label={`Organization: ${organizationName}`}
          >
            {organizationName}
          </span>
        )}

        {/* Retrieval mode selector */}
        <fieldset
          className="flex items-center gap-1 p-0.5 bg-surface-subtle rounded-lg border border-border"
          aria-label="Retrieval mode"
          disabled={isLoading}
        >
          <legend className="sr-only">Select retrieval mode</legend>

          {(['semantic', 'hybrid'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              role="radio"
              aria-checked={retrievalMode === mode}
              onClick={() => onRetrievalModeChange(mode)}
              disabled={isLoading}
              className={cn(
                'px-2.5 py-1 rounded text-xs font-medium transition-colors capitalize',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                retrievalMode === mode
                  ? 'bg-surface-elevated text-text-primary shadow-sm'
                  : 'text-text-secondary hover:text-text-primary',
              )}
              aria-label={`${mode === 'hybrid' ? 'Hybrid (semantic + graph)' : 'Semantic'} retrieval`}
            >
              {mode}
            </button>
          ))}
        </fieldset>

        {/* Clear conversation — only shown when there are messages */}
        {hasConversation && onClear && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            disabled={isLoading}
            aria-label="Clear conversation"
            data-testid="clear-chat-btn"
          >
            <UtilityIcons.Refresh className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Clear</span>
          </Button>
        )}
      </div>
    </header>
  );
}
