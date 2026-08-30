/**
 * ExplainabilityAccordion — collapsible "Why this answer?" section.
 *
 * AI UI Contract:
 *   - Collapsed by default (does NOT violate the contract — the mandatory always-
 *     visible fields are rendered by CitationPanel / ConfidenceBadge / RetrievalModeTag
 *     outside this accordion in AIResponseCard).
 *   - This accordion adds extra depth: plain-English summary, memory count,
 *     full graph traversal, and detailed citation breakdown.
 *   - Fully keyboard accessible via Radix Accordion.
 *   - Receives all data as props — no store or service reads.
 *
 * Location: features/explainability/ — not to be redefined elsewhere.
 */

import * as RadixAccordion from '@radix-ui/react-accordion';
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from 'react';
import { AIIcons, UtilityIcons } from '@config/icons';
import { ConfidenceBadge } from './ConfidenceBadge';
import { RetrievalModeTag } from './RetrievalModeTag';
import { GraphPathPanel } from './GraphPathPanel';
import { CitationPanel } from './CitationPanel';
import type { RetrievalExplanationRead } from '@typedefs/chat';
import { cn } from '@utils/cn';

// ─── Radix primitives (styled) ───────────────────────────────────────────────

const AccordionItem = forwardRef<
  ElementRef<typeof RadixAccordion.Item>,
  ComponentPropsWithoutRef<typeof RadixAccordion.Item>
>(({ className, ...props }, ref) => (
  <RadixAccordion.Item
    ref={ref}
    className={cn('border-t border-border', className)}
    {...props}
  />
));
AccordionItem.displayName = 'AccordionItem';

const AccordionTrigger = forwardRef<
  ElementRef<typeof RadixAccordion.Trigger>,
  ComponentPropsWithoutRef<typeof RadixAccordion.Trigger>
>(({ className, children, ...props }, ref) => (
  <RadixAccordion.Header>
    <RadixAccordion.Trigger
      ref={ref}
      className={cn(
        'flex items-center gap-2 w-full py-2 text-xs font-medium text-text-secondary',
        'hover:text-text-primary transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded',
        '[&[data-state=open]>svg:last-child]:rotate-180',
        className,
      )}
      {...props}
    >
      {children}
      <UtilityIcons.ChevronDown
        className="h-3.5 w-3.5 ml-auto transition-transform duration-200"
        aria-hidden="true"
      />
    </RadixAccordion.Trigger>
  </RadixAccordion.Header>
));
AccordionTrigger.displayName = 'AccordionTrigger';

const AccordionContent = forwardRef<
  ElementRef<typeof RadixAccordion.Content>,
  ComponentPropsWithoutRef<typeof RadixAccordion.Content>
>(({ className, children, ...props }, ref) => (
  <RadixAccordion.Content
    ref={ref}
    className={cn(
      'overflow-hidden text-xs',
      'data-[state=open]:animate-accordion-down',
      'data-[state=closed]:animate-accordion-up',
      className,
    )}
    {...props}
  >
    <div className="pb-3 space-y-3">{children}</div>
  </RadixAccordion.Content>
));
AccordionContent.displayName = 'AccordionContent';

// ─── ExplainabilityAccordion ─────────────────────────────────────────────────

interface ExplainabilityAccordionProps {
  explanation: RetrievalExplanationRead;
  /** Default open state — defaults to false (collapsed). */
  defaultOpen?: boolean;
  className?: string;
}

export function ExplainabilityAccordion({
  explanation,
  defaultOpen = false,
  className,
}: ExplainabilityAccordionProps) {
  return (
    <RadixAccordion.Root
      type="single"
      collapsible
      defaultValue={defaultOpen ? 'explanation' : undefined}
      className={cn('w-full', className)}
      data-testid="explainability-accordion"
    >
      <AccordionItem value="explanation">
        <AccordionTrigger aria-label="Show retrieval explanation">
          <AIIcons.granite className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span>Why this answer?</span>
          {/* Inline summary badges always visible inside trigger */}
          <span className="flex items-center gap-1.5 ml-2">
            <ConfidenceBadge score={explanation.confidence} className="text-[10px]" />
            <RetrievalModeTag mode={explanation.retrieval_mode} className="text-[10px]" />
          </span>
        </AccordionTrigger>

        <AccordionContent>
          <div
            className="space-y-4"
            aria-label="Retrieval explanation details"
          >
            {/* Plain-English summary */}
            {explanation.summary && (
              <div className="p-2.5 bg-surface-subtle rounded border border-border">
                <p className="text-xs text-text-secondary leading-relaxed">
                  {explanation.summary}
                </p>
              </div>
            )}

            {/* Stats row */}
            <div className="flex items-center gap-4 text-xs text-text-muted">
              <span>
                <strong className="text-text-primary">{explanation.result_count}</strong>
                {' '}memor{explanation.result_count === 1 ? 'y' : 'ies'} retrieved
              </span>
              <span>
                <strong className="text-text-primary">{explanation.citations.length}</strong>
                {' '}citation{explanation.citations.length === 1 ? '' : 's'}
              </span>
              {explanation.graph_path.length > 0 && (
                <span>
                  <strong className="text-text-primary">{explanation.graph_path.length}</strong>
                  {' '}graph step{explanation.graph_path.length === 1 ? '' : 's'}
                </span>
              )}
            </div>

            {/* Full citation breakdown */}
            <CitationPanel citations={explanation.citations} />

            {/* Graph traversal */}
            <GraphPathPanel steps={explanation.graph_path} />
          </div>
        </AccordionContent>
      </AccordionItem>
    </RadixAccordion.Root>
  );
}
