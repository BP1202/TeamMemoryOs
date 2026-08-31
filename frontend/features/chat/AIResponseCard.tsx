/**
 * AIResponseCard — single renderer for every assistant AI response.
 *
 * This is the canonical layout for all Granite-powered responses:
 *   1. Header  — Granite badge · RetrievalModeTag · ConfidenceBadge · timestamp
 *   2. Answer  — MarkdownRenderer (sanitized)
 *   3. Explainability — ExplainabilityAccordion ("Why this answer?")
 *   4. Suggested Actions — <button> elements only, never <a href>
 *
 * AI UI Contract (mandatory, non-negotiable):
 *   - ConfidenceBadge always visible in header.
 *   - RetrievalModeTag always visible in header.
 *   - CitationPanel always accessible (inside accordion).
 *   - GraphPathPanel visible when graph_path non-empty (inside accordion).
 *   - ParticipatingAgentsList visible when agents non-empty.
 *
 * Rules:
 *   - Pure display component — receives all data as props.
 *   - No store or service reads.
 *   - No dangerouslySetInnerHTML.
 *   - MessageBubble delegates assistant rendering here.
 *   - Reused by Engineering Copilot and Multi-Agent Workspace (Sprint 8.5).
 */

import { AIIcons, UtilityIcons } from '@config/icons';
import { MarkdownRenderer } from '@utils/markdownRenderer';
import { ConfidenceBadge } from '@features/explainability/ConfidenceBadge';
import { RetrievalModeTag } from '@features/explainability/RetrievalModeTag';
import { ParticipatingAgentsList } from '@features/explainability/ParticipatingAgentsList';
import { ExplainabilityAccordion } from '@features/explainability/ExplainabilityAccordion';
import type { RetrievalExplanationRead } from '@typedefs/chat';
import { cn } from '@utils/cn';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatTimestamp(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

// ─── Props ────────────────────────────────────────────────────────────────────

export interface AIResponseCardProps {
  /** The AI-generated answer text (Markdown). */
  content: string;
  /** Retrieval explanation from backend — enables all explainability fields. */
  explanation: RetrievalExplanationRead | null;
  /** Backend provider used (e.g. "ibm-granite"). Drives Granite badge visibility. */
  provider_used?: string;
  /** ISO timestamp of the response. */
  created_at?: string;
  /** Follow-up action suggestions — rendered as buttons only. */
  suggested_actions?: string[];
  /** Callback when the user clicks a suggested action. */
  onSuggestedAction?: (action: string) => void;
  /** Agents that participated (populated in multi-agent responses). */
  participating_agents?: string[];
  className?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function AIResponseCard({
  content,
  explanation,
  provider_used,
  created_at,
  suggested_actions = [],
  onSuggestedAction,
  participating_agents = [],
  className,
}: AIResponseCardProps) {
  const isGranite =
    !provider_used ||
    provider_used.toLowerCase().includes('granite') ||
    provider_used.toLowerCase().includes('ibm');

  return (
    <article
      className={cn('space-y-3', className)}
      aria-label="AI response"
      data-testid="ai-response-card"
    >
      {/* ── Section 1: Header ───────────────────────────────────────────── */}
      <header
        className="flex items-center gap-2 flex-wrap"
        aria-label="Response metadata"
      >
        {/* IBM Granite attribution badge */}
        {isGranite && (
          <span
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-brand/10 text-brand border border-brand/20"
            aria-label="Powered by IBM Granite"
            title="Powered by IBM Granite"
          >
            <AIIcons.granite className="h-3 w-3" aria-hidden="true" />
            Granite
          </span>
        )}

        {/* Retrieval mode — always visible */}
        {explanation && (
          <RetrievalModeTag mode={explanation.retrieval_mode} />
        )}

        {/* Confidence — always visible */}
        {explanation && (
          <ConfidenceBadge score={explanation.confidence} />
        )}

        {/* Timestamp */}
        {created_at && (
          <time
            dateTime={created_at}
            className="ml-auto text-[10px] text-text-muted"
            aria-label={`Sent at ${formatTimestamp(created_at)}`}
          >
            {formatTimestamp(created_at)}
          </time>
        )}
      </header>

      {/* ── Section 2: Answer ───────────────────────────────────────────── */}
      <div className="text-sm text-text-primary">
        <MarkdownRenderer content={content} />
      </div>

      {/* ── Section 3: Explainability ────────────────────────────────────── */}
      {explanation && (
        <ExplainabilityAccordion
          explanation={explanation}
          defaultOpen={false}
          data-testid="explainability-panel"
        />
      )}

      {/* Participating agents — visible when non-empty */}
      {participating_agents.length > 0 && (
        <ParticipatingAgentsList agents={participating_agents} />
      )}

      {/* ── Section 4: Suggested Actions ─────────────────────────────────── */}
      {suggested_actions.length > 0 && (
        <nav
          className="flex flex-wrap gap-2 pt-1"
          aria-label="Suggested follow-up questions"
        >
          {suggested_actions.map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => onSuggestedAction?.(action)}
              className={cn(
                'px-3 py-1.5 text-xs rounded-lg border border-border',
                'bg-surface-subtle text-text-secondary',
                'hover:bg-surface-elevated hover:text-text-primary transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
              )}
              aria-label={`Ask: ${action}`}
            >
              <UtilityIcons.ArrowRight
                className="h-3 w-3 inline-block mr-1"
                aria-hidden="true"
              />
              {action}
            </button>
          ))}
        </nav>
      )}
    </article>
  );
}
